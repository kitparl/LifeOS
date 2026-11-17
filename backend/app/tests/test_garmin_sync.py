"""Garmin Personal API sync: key handling, first and later syncs, failures, and the response mapping.

FakeGarmin answers the same paths with the same response shapes as the real API (values are made up).
"""

import json
from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qs

import httpx
import pytest
from app.core import database
from app.core.timezone import utc_now
from app.modules.health.contracts import SOURCE_GARMIN
from app.modules.health.models import HealthDay, HealthMeasurement
from app.modules.integrations.garmin import health_mapping, personal_api
from app.modules.integrations.garmin.import_service import wait_for_imports
from app.modules.integrations.garmin.sync_service import (
    OVERLAP_DAYS,
    REASON_KEY_REFUSED,
    REASON_THROTTLED,
    sync_all_enabled,
)
from app.modules.integrations.models import IntegrationConnection
from app.modules.notifications.models import Notification
from app.tests.test_garmin_import import api, fit, register, runs_of, zip_of  # noqa: F401  (fixture and helpers)
from sqlalchemy import func, select

CONNECTION = "/api/v1/integrations/garmin/connection"
SYNC = "/api/v1/integrations/garmin/sync"
IMPORTS = "/api/v1/integrations/garmin/imports"
KEY = "personal-key-abcdef-1234"
TOKEN = "eyJhbGciOiJub25lIn0.eyJleHAiOjB9.sig"  # shape of a JWT; contents are irrelevant here


def _day(days_ago: int) -> date:
    return utc_now().date() - timedelta(days=days_ago)


def _local_ms(day: date, hour: int, minute: int) -> int:
    """Garmin's '...TimestampLocal' style: local clock time stored as if it were UTC."""
    return int(datetime(day.year, day.month, day.day, hour, minute, tzinfo=timezone.utc).timestamp() * 1000)


def summary(day: date, steps: int = 8000) -> dict:
    return {
        "calendarDate": day.isoformat(),
        "movement": {"steps": {"value": steps, "distanceInMeters": 6400.0}, "floorsAscended": {"value": 6}},
        "calories": {"burnedResting": 1700, "burnedActive": 420, "burnedTotal": 2120},
        "heartRate": {"minValue": 52, "maxValue": 160, "restingValue": 58},
        "intensityMinutes": {"moderate": 20, "vigorous": 35},
        "stress": {"avgLevel": 31, "maxLevel": 90},
        "bodyBattery": {"minValue": 20, "maxValue": 85},
        "respiration": {"avgValue": 15},
    }


def sleep(day: date) -> dict:
    return {
        "calendarDate": day.isoformat(),
        "sleepTimeSeconds": 25200,
        "deepSleepSeconds": 5400,
        "lightSleepSeconds": 14400,
        "remSleepSeconds": 5400,
        "awakeSleepSeconds": 900,
        "sleepStartTimestampLocal": _local_ms(day - timedelta(days=1), 23, 15),
        "sleepEndTimestampLocal": _local_ms(day, 6, 40),
        "sleepScores": {"overall": {"value": 82}},
    }


class FakeGarmin:
    """Routes Personal API requests by path and records them. Tests edit the public fields."""

    def __init__(self) -> None:
        self.key = KEY
        self.activities: list[tuple[int, date, bytes]] = []
        self.summaries: dict[date, dict] = {}
        self.sleep: dict[date, dict] = {}
        self.hrv: dict[date, float] = {}
        self.weights: list[dict] = []
        self.failures: dict[str, int] = {}  # path prefix -> HTTP status
        self.calls: list[str] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        self.calls.append(path + ("?" + request.url.query.decode() if request.url.query else ""))
        for prefix, code in self.failures.items():
            if path.startswith(prefix) or self.calls[-1].startswith(prefix):
                return httpx.Response(code)
        if path == personal_api.TOKEN_PATH:
            ok = request.method == "POST" and request.headers.get("Authorization") == f"ApiKey {self.key}"
            return httpx.Response(200, text=TOKEN) if ok else httpx.Response(401)
        if request.headers.get("Authorization") != f"Bearer {TOKEN}":
            return httpx.Response(401)
        query = {k: v[0] for k, v in parse_qs(request.url.query.decode()).items()}
        return self._route(path, query)

    def _route(self, path: str, q: dict[str, str]) -> httpx.Response:
        if path == "/activitylist-service/activities/search/activities":
            lo, hi = date.fromisoformat(q["startDate"]), date.fromisoformat(q["endDate"])
            found = [{"activityId": i} for i, day, _ in self.activities if lo <= day <= hi]
            start, limit = int(q["start"]), int(q["limit"])
            return httpx.Response(200, json=found[start : start + limit])
        if path.startswith("/download-service/files/activity/"):
            wanted = int(path.rsplit("/", 1)[1])
            data = next((d for i, _, d in self.activities if i == wanted), None)
            return httpx.Response(200, content=data) if data else httpx.Response(404)
        if path == "/usersummary-service/v2/dailysummaries":
            lo, hi = date.fromisoformat(q["startDate"]), date.fromisoformat(q["endDate"])
            return httpx.Response(200, json={"data": [v for d, v in sorted(self.summaries.items()) if lo <= d <= hi]})
        if path == "/sleep-service/sleep/dailySleep":
            day = date.fromisoformat(q["date"])
            return httpx.Response(200, json=self.sleep.get(day, {"calendarDate": None, "sleepTimeSeconds": None}))
        if path.startswith("/hrv-service/hrv/daily/"):
            lo, hi = (date.fromisoformat(x) for x in path.split("/")[-2:])
            items = [{"calendarDate": d.isoformat(), "lastNightAvg": v} for d, v in self.hrv.items() if lo <= d <= hi]
            return httpx.Response(200, json={"hrvSummaries": items})
        if path.startswith("/wellness-service/wellness/daily/spo2acclimation/"):
            return httpx.Response(200, json={"averageSpO2": None, "lowestSpO2": None})
        if path.startswith("/weight-service/weight/range/"):
            return httpx.Response(200, json={"dailyWeightSummaries": [{"allWeightMetrics": self.weights}]})
        return httpx.Response(404)

    def sleep_dates(self) -> list[str]:
        return [c.split("date=")[1] for c in self.calls if c.startswith("/sleep-service/sleep/dailySleep")]


@pytest.fixture
def garmin(monkeypatch):
    fake = FakeGarmin()
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        personal_api, "_http_client", lambda timeout: real_client(timeout=timeout, transport=httpx.MockTransport(fake.handle))
    )
    monkeypatch.setattr(personal_api, "REQUEST_PAUSE_SECONDS", 0)
    return fake


async def connect(client, headers, key: str = KEY):
    response = await client.put(CONNECTION, headers=headers, json={"api_key": key})
    await wait_for_imports()
    return response


async def jobs_of(client, headers) -> list[dict]:
    return (await client.get(IMPORTS, headers=headers)).json()


# --- Mapping (pure) ---------------------------------------------------------------------------


def test_summary_mapping_reads_every_metric_and_converts_units():
    day = date(2026, 3, 4)
    values = health_mapping.summary_days({"data": [summary(day)]})[day]
    assert values == {
        "steps": 8000, "distance_km": 6.4, "floors": 6, "active_calories": 420, "total_calories": 2120,
        "min_hr": 52, "max_hr": 160, "resting_hr": 58, "intensity_min_moderate": 20, "intensity_min_vigorous": 35,
        "stress_avg": 31, "stress_max": 90, "body_battery_high": 85, "body_battery_low": 20, "respiration_avg": 15.0,
    }


def test_sleep_mapping_gives_minutes_score_and_local_clock_times():
    day = date(2026, 3, 4)
    assert health_mapping.sleep_values(sleep(day)) == {
        "sleep_total_min": 420, "sleep_deep_min": 90, "sleep_light_min": 240, "sleep_rem_min": 90,
        "sleep_awake_min": 15, "sleep_score": 82, "bed_time_min": 23 * 60 + 15, "wake_time_min": 6 * 60 + 40,
    }


def test_mapping_drops_missing_malformed_and_out_of_range_values_without_losing_the_day():
    day = date(2026, 3, 4)
    raw = {"calendarDate": day.isoformat(), "heartRate": {"restingValue": 900, "maxValue": "fast"}, "stress": {"avgLevel": -1},
           "movement": {"steps": {"value": True}}, "bodyBattery": {"maxValue": 70}}
    assert health_mapping.summary_days({"data": [raw, {"calendarDate": "not a date"}]}) == {day: {"body_battery_high": 70}}
    assert health_mapping.sleep_values({"calendarDate": None, "sleepTimeSeconds": None}) == {}
    assert health_mapping.spo2_values({"averageSpO2": None, "lowestSpO2": None}) == {}
    assert health_mapping.summary_days(None) == {} and health_mapping.hrv_days([]) == {}


def test_merge_combines_sources_per_date_and_skips_empty_dates():
    a, b = date(2026, 3, 4), date(2026, 3, 5)
    merged = health_mapping.merge_days({a: {"steps": 10}}, {a: {"hrv_ms": 40.0}, b: {}})
    assert [(d.day, d.values) for d in merged] == [(a, {"steps": 10, "hrv_ms": 40.0})]


def test_weight_mapping_converts_grams_and_adds_body_composition_only_when_measured():
    stamp = 1_772_000_000_000
    readings = health_mapping.weight_measurements(
        {"dailyWeightSummaries": [{"allWeightMetrics": [
            {"samplePk": 1, "date": stamp, "weight": 74000.0, "bmi": 24.16, "bodyFat": None, "muscleMass": None},
            {"samplePk": 2, "date": stamp, "weight": 73550.0, "bmi": 24.0, "bodyFat": 18.25, "muscleMass": 33100.0},
            {"samplePk": 3, "date": None, "weight": 70000.0},
        ]}]}
    )
    assert [(r.kind, r.values, r.external_id) for r in readings] == [
        ("weight", {"weight_kg": 74.0}, "1"),
        ("weight", {"weight_kg": 73.55}, "2"),
        ("body_comp", {"body_fat_pct": 18.2, "muscle_mass_kg": 33.1, "bmi": 24.0}, "2:body"),
    ]


# --- Key handling -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_refused_key_is_not_stored(api, garmin):  # noqa: F811
    headers, _ = await register(api, "gkeybad")
    response = await connect(api, headers, key="wrong-key-000000")
    assert response.status_code == 400
    assert (await api.get(CONNECTION, headers=headers)).json()["connected"] is False
    assert await jobs_of(api, headers) == []


@pytest.mark.asyncio
async def test_sync_needs_a_key_first(api, garmin):  # noqa: F811
    headers, _ = await register(api, "gnokey")
    assert (await api.post(SYNC, headers=headers)).status_code == 400


@pytest.mark.asyncio
async def test_key_is_stored_encrypted_and_never_returned(api, garmin, caplog):  # noqa: F811
    headers, user_id = await register(api, "gkeysafe")
    status = (await connect(api, headers)).json()
    assert status["connected"] is True and status["key_masked"] == "****1234"
    async with api.session_factory() as db:
        stored = (await db.execute(select(IntegrationConnection.config_json).where(
            IntegrationConnection.user_id == user_id, IntegrationConnection.provider == "garmin"))).scalar_one()
    listed = (await api.get("/api/v1/integrations", headers=headers)).json()
    everything = json.dumps(listed) + stored + json.dumps(status) + caplog.text
    assert KEY not in everything and TOKEN not in everything
    assert [c["config_json"] for c in listed if c["provider"] == "garmin"] == [None]


# --- Syncing ----------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_first_sync_pulls_twelve_months_of_activities_and_health(api, garmin):  # noqa: F811
    headers, user_id = await register(api, "gfirst")
    garmin.activities = [(9001, _day(3), zip_of({"9001_ACTIVITY.fit": fit(9001, days_ago=3)}))]
    garmin.summaries = {_day(1): summary(_day(1)), _day(200): summary(_day(200), steps=5000)}
    garmin.sleep = {_day(1): sleep(_day(1))}
    garmin.hrv = {_day(1): 45.0}
    garmin.weights = [{"samplePk": 77, "date": 1_772_000_000_000, "weight": 74000.0, "bmi": 24.2}]

    await connect(api, headers)

    [job] = await jobs_of(api, headers)
    assert (job["origin"], job["range_mode"], job["status"]) == ("sync", "12m", "finished")
    assert (job["created"], job["runs_created"], job["health_days"]) == (1, 1, 2)
    assert len(await runs_of(api, headers)) == 1
    assert garmin.sleep_dates()[0] == (_day(365)).isoformat()
    async with api.session_factory() as db:
        day = (await db.execute(select(HealthDay).where(HealthDay.user_id == user_id, HealthDay.date == _day(1)))).scalar_one()
        weights = (await db.execute(select(func.count()).select_from(HealthMeasurement).where(
            HealthMeasurement.user_id == user_id, HealthMeasurement.source == SOURCE_GARMIN))).scalar_one()
    assert (day.source, day.steps, day.sleep_total_min, day.hrv_ms, day.resting_hr) == (SOURCE_GARMIN, 8000, 420, 45.0, 58)
    assert weights == 1
    status = (await api.get(CONNECTION, headers=headers)).json()
    assert status["last_sync_ok"] is True and status["synced_through"] is not None
    assert status["last_sync_message"] == "Synced 1 new activity, 2 health days."


@pytest.mark.asyncio
async def test_later_syncs_read_only_recent_days_and_never_duplicate(api, garmin):  # noqa: F811
    headers, _ = await register(api, "glater")
    garmin.activities = [(9101, _day(1), zip_of({"a.fit": fit(9101, days_ago=1)}))]
    garmin.weights = [{"samplePk": 5, "date": 1_772_000_000_000, "weight": 74000.0}]
    await connect(api, headers)
    synced_through = date.fromisoformat((await api.get(CONNECTION, headers=headers)).json()["synced_through"])
    garmin.calls.clear()

    response = await api.post(SYNC, headers=headers)
    assert response.status_code == 202
    await wait_for_imports()

    latest = (await jobs_of(api, headers))[0]
    assert (latest["range_mode"], latest["status"], latest["created"], latest["duplicates"]) == ("recent", "finished", 0, 1)
    assert garmin.sleep_dates()[0] == (synced_through - timedelta(days=OVERLAP_DAYS)).isoformat()
    assert len(await runs_of(api, headers)) == 1


@pytest.mark.asyncio
async def test_a_failed_download_is_reported_and_the_rest_continue(api, garmin):  # noqa: F811
    headers, _ = await register(api, "gdl")
    garmin.activities = [
        (9201, _day(2), b""),  # Garmin answers 404 for this one
        (9202, _day(2), zip_of({"b.fit": fit(9202, days_ago=2)})),
    ]
    await connect(api, headers)
    [job] = await jobs_of(api, headers)
    assert (job["status"], job["created"], job["failed"]) == ("finished", 1, 1)
    assert job["errors"] == [{"name": "Garmin activity 9201", "reason": "Could not download this activity from Garmin"}]


@pytest.mark.asyncio
async def test_a_refused_key_stops_the_sync_pauses_it_and_notifies_once(api, garmin):  # noqa: F811
    headers, user_id = await register(api, "grevoked")
    await connect(api, headers)
    garmin.key = "rotated-key-999999"  # the user deleted or replaced the key on Garmin

    await api.post(SYNC, headers=headers)
    await wait_for_imports()

    latest = (await jobs_of(api, headers))[0]
    assert (latest["status"], latest["error"]) == ("failed", REASON_KEY_REFUSED)
    status = (await api.get(CONNECTION, headers=headers)).json()
    assert (status["connected"], status["status"], status["last_sync_ok"]) == (False, "error", False)
    assert (await api.post(SYNC, headers=headers)).status_code == 400  # paused until a new key is added
    async with api.session_factory() as db:
        notes = (await db.execute(select(Notification.message, Notification.route).where(Notification.user_id == user_id))).all()
    assert [tuple(n) for n in notes] == [("Garmin sync stopped: add a new Garmin key", "/integrations")]


@pytest.mark.asyncio
async def test_throttling_keeps_finished_days_and_the_next_sync_resumes(api, garmin):  # noqa: F811
    headers, _ = await register(api, "gthrottle")
    stop_at = _day(300)
    garmin.failures = {f"/sleep-service/sleep/dailySleep?date={stop_at.isoformat()}": 429}

    await connect(api, headers)

    [job] = await jobs_of(api, headers)
    assert (job["status"], job["error"]) == ("failed", REASON_THROTTLED)
    cursor = date.fromisoformat((await api.get(CONNECTION, headers=headers)).json()["synced_through"])
    assert _day(365) <= cursor < stop_at

    garmin.failures.clear()
    garmin.calls.clear()
    await api.post(SYNC, headers=headers)
    await wait_for_imports()
    assert (await jobs_of(api, headers))[0]["status"] == "finished"
    assert garmin.sleep_dates()[0] == (cursor - timedelta(days=OVERLAP_DAYS)).isoformat()


@pytest.mark.asyncio
async def test_disconnect_forgets_the_key_and_keeps_the_data(api, garmin):  # noqa: F811
    headers, _ = await register(api, "gdisc")
    garmin.activities = [(9301, _day(2), zip_of({"c.fit": fit(9301, days_ago=2)}))]
    await connect(api, headers)

    assert (await api.delete(CONNECTION, headers=headers)).status_code == 204
    assert (await api.get(CONNECTION, headers=headers)).json()["connected"] is False
    assert len(await runs_of(api, headers)) == 1


@pytest.mark.asyncio
async def test_generic_integration_endpoints_cannot_enable_garmin_without_a_key(api, garmin):  # noqa: F811
    headers, _ = await register(api, "ggeneric")
    created = await api.post("/api/v1/integrations", headers=headers, json={"provider": "garmin", "enabled": True})
    assert created.status_code == 201 and created.json()["enabled"] is False
    patched = await api.patch(f"/api/v1/integrations/{created.json()['id']}", headers=headers, json={"enabled": True})
    assert patched.status_code == 400


@pytest.mark.asyncio
async def test_scheduled_sync_runs_for_every_connected_user(api, garmin, monkeypatch):  # noqa: F811
    headers, _ = await register(api, "gsched")
    await connect(api, headers)
    monkeypatch.setattr(database, "async_session_factory", api.session_factory)

    await sync_all_enabled()

    jobs = await jobs_of(api, headers)
    assert [(j["origin"], j["range_mode"], j["status"]) for j in jobs] == [
        ("sync", "recent", "finished"), ("sync", "12m", "finished"),
    ]


@pytest.mark.asyncio
async def test_dates_without_data_answered_with_no_content_do_not_stop_the_sync(api, garmin):  # noqa: F811
    headers, _ = await register(api, "gempty")
    garmin.summaries = {_day(1): summary(_day(1))}
    garmin.failures = {"/sleep-service/sleep/dailySleep": 204, "/hrv-service/": 204, "/wellness-service/": 204}

    await connect(api, headers)

    [job] = await jobs_of(api, headers)
    assert (job["status"], job["error"], job["health_days"]) == ("finished", None, 1)


@pytest.mark.asyncio
async def test_an_unexpected_garmin_error_names_the_status_and_endpoint(api, garmin):  # noqa: F811
    headers, _ = await register(api, "gerror")
    garmin.failures = {"/sleep-service/sleep/dailySleep": 500}

    await connect(api, headers)

    [job] = await jobs_of(api, headers)
    assert job["status"] == "failed"
    assert job["error"] == (
        "Garmin returned an error (HTTP 500 on /sleep-service/sleep/dailySleep). The next sync will try again."
    )
    status = (await api.get(CONNECTION, headers=headers)).json()
    assert status["last_sync_message"] == job["error"] and status["connected"] is True
