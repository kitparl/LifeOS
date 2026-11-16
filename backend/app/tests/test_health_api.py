"""Health API: manual entry, merge, Today, trends, sleep, measurements, imports, ownership (Unit 4)."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import app.modules.activities
import app.modules.ai
import app.modules.memory
import app.modules.qa
import app.modules.search
import pytest
from app.modules.auth.models import User
from app.modules.health.contracts import ParsedHealthDay
from app.modules.health.service import HealthService
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import select

API = "/api/v1/health"


async def register(client, name: str = "healthuser") -> tuple[dict, str]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": name, "email": f"{name}@example.com", "password": "password123", "display_name": "H"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    async with client.session_factory() as db:
        user_id = (await db.execute(select(User.id).where(User.username == name))).scalar_one()
    return headers, user_id


def today() -> date:
    return datetime.now(timezone.utc).date()  # the test user's timezone is UTC


async def put_day(client, headers, day: date, values: dict):
    return await client.put(f"{API}/days/{day}", headers=headers, json={"values": values})


async def seed(client, user_id: str, source: str, days: dict[date, dict]):
    async with client.session_factory() as db:
        await HealthService(db).bulk_upsert_days(user_id, source, [ParsedHealthDay(d, v) for d, v in days.items()])
        await db.commit()


@pytest.mark.asyncio
async def test_catalogue_lists_every_metric_with_its_limits(client):
    headers, _ = await register(client)
    metrics = (await client.get(f"{API}/metrics", headers=headers)).json()
    by_key = {m["key"]: m for m in metrics}

    assert by_key["resting_hr"] == {
        "key": "resting_hr", "label": "Resting heart rate", "unit": "bpm", "group": "heart", "kind": "int",
        "min": 20.0, "max": 150.0, "lower_is_better": True, "today": True,
    }
    assert sum(1 for m in metrics if m["today"]) == 5


@pytest.mark.asyncio
async def test_manual_entry_is_saved_updated_and_cleared_without_duplicates(client):
    headers, _ = await register(client)
    day = today() - timedelta(days=1)

    first = await put_day(client, headers, day, {"sleep_total_min": 420, "resting_hr": 52})
    second = await put_day(client, headers, day, {"resting_hr": 50, "hrv_ms": 48.5})
    cleared = await put_day(client, headers, day, {"sleep_total_min": None})
    days = (await client.get(f"{API}/days", headers=headers, params={"start": str(day), "end": str(day)})).json()

    assert first.status_code == 200 and first.json()["values"] == {"sleep_total_min": 420, "resting_hr": 52}
    assert second.json()["values"] == {"sleep_total_min": 420, "resting_hr": 50, "hrv_ms": 48.5}
    assert cleared.json()["values"] == {"resting_hr": 50, "hrv_ms": 48.5}
    assert set(cleared.json()["sources"].values()) == {"manual"}
    assert len(days) == 1


@pytest.mark.asyncio
async def test_values_outside_the_allowed_range_or_type_are_rejected_naming_the_field(client):
    headers, _ = await register(client)
    day = today()

    too_high = await put_day(client, headers, day, {"resting_hr": 400})
    unknown = await put_day(client, headers, day, {"is_admin": 1})
    text = await put_day(client, headers, day, {"resting_hr": "fast"})
    boolean = await put_day(client, headers, day, {"steps": True})
    future = await put_day(client, headers, day + timedelta(days=3), {"steps": 1})

    assert too_high.status_code == 422 and "Resting heart rate" in too_high.text
    assert unknown.status_code == 422 and text.status_code == 422 and boolean.status_code == 422
    assert future.status_code == 400
    assert (await client.get(f"{API}/days/{day}", headers=headers)).status_code == 404


@pytest.mark.asyncio
async def test_manual_values_take_precedence_over_garmin_field_by_field(client):
    headers, user_id = await register(client)
    day = today() - timedelta(days=2)
    await seed(client, user_id, "garmin", {day: {"resting_hr": 60, "steps": 9000, "hrv_ms": 45.0}})
    await put_day(client, headers, day, {"resting_hr": 50})

    merged = (await client.get(f"{API}/days/{day}", headers=headers)).json()

    assert merged["values"] == {"resting_hr": 50, "steps": 9000, "hrv_ms": 45.0}
    assert merged["sources"] == {"resting_hr": "manual", "steps": "garmin", "hrv_ms": "garmin"}


@pytest.mark.asyncio
async def test_reimporting_a_garmin_day_replaces_it_and_leaves_manual_data_alone(client):
    headers, user_id = await register(client)
    day = today() - timedelta(days=2)
    await put_day(client, headers, day, {"resting_hr": 50})
    await seed(client, user_id, "garmin", {day: {"steps": 9000, "hrv_ms": 45.0}})

    async with client.session_factory() as db:
        counts = await HealthService(db).bulk_upsert_days(user_id, "garmin", [ParsedHealthDay(day, {"steps": 9500})])
        await db.commit()

    merged = (await client.get(f"{API}/days/{day}", headers=headers)).json()
    assert (counts.created, counts.updated) == (0, 1)
    assert merged["values"] == {"resting_hr": 50, "steps": 9500}  # hrv replaced by the new import (absent now)


@pytest.mark.asyncio
async def test_bulk_upsert_refuses_manual_and_validates_values(client):
    _, user_id = await register(client)
    async with client.session_factory() as db:
        service = HealthService(db)
        with pytest.raises(Exception, match="Manual data"):
            await service.bulk_upsert_days(user_id, "manual", [ParsedHealthDay(today(), {"steps": 1})])
        with pytest.raises(ValueError):
            await service.bulk_upsert_days(user_id, "garmin", [ParsedHealthDay(today(), {"resting_hr": 999})])


@pytest.mark.asyncio
async def test_today_shows_values_against_the_personal_baseline(client):
    headers, user_id = await register(client)
    latest = today() - timedelta(days=1)
    history = {latest - timedelta(days=i): {"resting_hr": 52, "hrv_ms": 50.0, "sleep_total_min": 420} for i in range(1, 15)}
    history[latest] = {"resting_hr": 58, "hrv_ms": 50.0, "sleep_total_min": 300, "stress_avg": 30}
    await seed(client, user_id, "garmin", history)

    response = (await client.get(f"{API}/today", headers=headers)).json()
    metrics = {m["key"]: m for m in response["metrics"]}

    assert response["day"] == str(latest) and response["is_today"] is False
    assert metrics["resting_hr"]["value"] == 58 and metrics["resting_hr"]["avg_30d"] == 52.0
    assert (metrics["resting_hr"]["marker"], metrics["resting_hr"]["favourable"]) == ("up", "bad")
    assert (metrics["sleep_total_min"]["marker"], metrics["sleep_total_min"]["favourable"]) == ("down", "bad")
    assert metrics["hrv_ms"]["marker"] == "flat" and metrics["hrv_ms"]["favourable"] is None
    assert metrics["stress_avg"]["needs_more_data"] is True and metrics["stress_avg"]["marker"] is None


@pytest.mark.asyncio
async def test_today_without_enough_history_has_no_baseline_and_with_no_data_is_empty(client):
    headers, _ = await register(client)
    assert (await client.get(f"{API}/today", headers=headers)).json() == {"day": None, "is_today": False, "metrics": []}

    await put_day(client, headers, today(), {"resting_hr": 55})
    metric = next(m for m in (await client.get(f"{API}/today", headers=headers)).json()["metrics"] if m["key"] == "resting_hr")

    assert (metric["value"], metric["avg_30d"], metric["marker"], metric["needs_more_data"]) == (55, None, None, True)


@pytest.mark.asyncio
async def test_trends_keep_gaps_as_gaps_and_add_a_rolling_average(client):
    headers, user_id = await register(client)
    end = today()
    await seed(client, user_id, "garmin", {end - timedelta(days=6): {"resting_hr": 60}, end - timedelta(days=2): {"resting_hr": 50}})

    series = (await client.get(f"{API}/metrics/resting_hr", headers=headers, params={"range": "7d"})).json()

    assert (series["start"], series["end"], len(series["points"])) == (str(end - timedelta(days=6)), str(end), 7)
    values = [p["value"] for p in series["points"]]
    assert values == [60.0, None, None, None, 50.0, None, None]
    assert (series["average"], series["minimum"], series["maximum"]) == (55.0, 50.0, 60.0)
    rolling = [p["value"] for p in series["rolling"]]
    assert rolling == [60.0, 60.0, 60.0, None, 50.0, 50.0, 50.0]  # mean of the values in the 3 days ending on each day
    assert (await client.get(f"{API}/metrics/nonsense", headers=headers)).status_code == 404
    assert (await client.get(f"{API}/metrics/steps", headers=headers, params={"range": "5y"})).status_code == 422


@pytest.mark.asyncio
async def test_range_queries_are_bounded(client):
    headers, _ = await register(client)
    too_long = await client.get(f"{API}/days", headers=headers, params={"start": "2024-01-01", "end": "2026-01-01"})
    backwards = await client.get(f"{API}/days", headers=headers, params={"start": "2026-02-01", "end": "2026-01-01"})
    assert too_long.status_code == 400 and backwards.status_code == 400


@pytest.mark.asyncio
async def test_sleep_view_lists_nights_with_stages_and_consistency(client):
    headers, user_id = await register(client)
    end = today()
    nights = {
        end - timedelta(days=i): {"sleep_total_min": 400 + i, "sleep_deep_min": 80, "bed_time_min": 1380 + 5 * i, "wake_time_min": 400}
        for i in range(1, 6)
    }
    await seed(client, user_id, "garmin", nights)
    await put_day(client, headers, end, {"steps": 100})  # a day with no sleep data is not a night

    sleep = (await client.get(f"{API}/sleep", headers=headers, params={"range": "7d"})).json()

    assert sleep["consistency"]["nights"] == 5 and len(sleep["nights"]) == 5
    assert sleep["consistency"]["wake_time_sd_min"] == 0.0
    assert 0 < sleep["consistency"]["bed_time_sd_min"] < 10
    assert sleep["nights"][0]["values"]["sleep_deep_min"] == 80


@pytest.mark.asyncio
async def test_measurements_are_validated_listed_newest_first_and_deletable(client):
    headers, _ = await register(client)
    now = datetime.now(timezone.utc)
    body = lambda kg, when: {"kind": "weight", "values": {"weight_kg": kg}, "measured_at": when.isoformat()}  # noqa: E731

    first = await client.post(f"{API}/measurements", headers=headers, json=body(72.5, now - timedelta(days=1)))
    same_day_a = await client.post(f"{API}/measurements", headers=headers, json=body(72.0, now))
    same_day_b = await client.post(f"{API}/measurements", headers=headers, json=body(72.2, now - timedelta(minutes=5)))
    bad = await client.post(f"{API}/measurements", headers=headers, json={"kind": "weight", "values": {"weight_kg": 3}})
    unknown_kind = await client.post(f"{API}/measurements", headers=headers, json={"kind": "mood", "values": {"x": 1}})
    future = await client.post(f"{API}/measurements", headers=headers, json=body(70, now + timedelta(days=5)))
    pressure = await client.post(
        f"{API}/measurements", headers=headers, json={"kind": "blood_pressure", "values": {"systolic": 118, "diastolic": 76}}
    )

    listed = (
        await client.get(f"{API}/measurements", headers=headers, params={"kind": "weight", "start": str((now - timedelta(days=3)).date()), "end": str(now.date())})
    ).json()

    assert [r.status_code for r in (first, same_day_a, same_day_b, pressure)] == [201, 201, 201, 201]
    assert (bad.status_code, unknown_kind.status_code, future.status_code) == (422, 422, 400)
    assert [m["values"]["weight_kg"] for m in listed] == [72.0, 72.2, 72.5]
    assert pressure.json()["values"] == {"systolic": 118.0, "diastolic": 76.0}
    assert (await client.delete(f"{API}/measurements/{first.json()['id']}", headers=headers)).status_code == 204
    after = (await client.get(f"{API}/measurements", headers=headers, params={"kind": "weight", "start": str((now - timedelta(days=3)).date()), "end": str(now.date())})).json()
    assert len(after) == 2


@pytest.mark.asyncio
async def test_another_user_sees_none_of_my_health_data(client):
    headers, user_id = await register(client)
    day = today() - timedelta(days=1)
    await put_day(client, headers, day, {"resting_hr": 50})
    weight = (await client.post(f"{API}/measurements", headers=headers, json={"kind": "weight", "values": {"weight_kg": 70}})).json()
    stranger, _ = await register(client, "stranger")

    assert (await client.get(f"{API}/days/{day}", headers=stranger)).status_code == 404
    assert (await client.get(f"{API}/days", headers=stranger, params={"start": str(day), "end": str(day)})).json() == []
    assert (await client.get(f"{API}/today", headers=stranger)).json()["day"] is None
    assert (await client.delete(f"{API}/measurements/{weight['id']}", headers=stranger)).status_code == 404
    for path in (f"{API}/today", f"{API}/days/{day}", f"{API}/sleep", f"{API}/metrics"):
        assert (await client.get(path)).status_code in (401, 403)
    assert (await client.get(f"{API}/days/{day}", headers=headers)).status_code == 200


@pytest.mark.asyncio
async def test_deleting_imported_data_can_include_garmin_health_but_never_manual_data(client):
    headers, user_id = await register(client)
    day = today() - timedelta(days=2)
    await put_day(client, headers, day, {"resting_hr": 50})
    await seed(client, user_id, "garmin", {day: {"steps": 9000}, day - timedelta(days=1): {"steps": 8000}})

    summary = (await client.get("/api/v1/integrations/garmin/data/summary", headers=headers)).json()
    assert summary["health_days"] == 2  # Garmin rows only; the manual row is not counted

    without = await client.delete("/api/v1/integrations/garmin/data", headers=headers)
    assert without.json()["health_days_deleted"] == 0
    assert len((await client.get(f"{API}/days", headers=headers, params={"start": str(day - timedelta(days=1)), "end": str(day)})).json()) == 2

    with_health = await client.delete("/api/v1/integrations/garmin/data", headers=headers, params={"include_health": "true"})

    assert with_health.json()["health_days_deleted"] == 2
    kept = (await client.get(f"{API}/days/{day}", headers=headers)).json()
    assert kept["values"] == {"resting_hr": 50}  # the manual row stays
    async with client.session_factory() as db:
        with pytest.raises(Exception, match="cannot be removed"):
            await HealthService(db).delete_by_source(user_id, "manual")


def test_health_data_is_unreachable_from_ai_memory_search_and_qa():
    """NFR-6: these modules never import the health or activity modules."""
    offenders = []
    for package in (app.modules.ai, app.modules.memory, app.modules.search, app.modules.qa):
        for path in Path(next(iter(package.__path__))).rglob("*.py"):
            text = path.read_text()
            if "modules.health" in text or "modules.activities" in text:
                offenders.append(str(path))
    assert offenders == []


@given(
    values=st.fixed_dictionaries(
        {},
        optional={
            "resting_hr": st.integers(20, 150),
            "hrv_ms": st.floats(1, 300, allow_nan=False, allow_infinity=False).map(lambda v: round(v, 2)),
            "steps": st.integers(0, 200_000),
            "sleep_score": st.integers(0, 100),
            "bed_time_min": st.integers(0, 1439),
        },
    )
)
@settings(max_examples=40, deadline=None)
def test_values_written_for_a_day_read_back_unchanged(values):
    import asyncio

    from app.core.database import Base
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    async def work():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        try:
            async with async_sessionmaker(engine, expire_on_commit=False)() as db:
                user = User(email="p@example.com", username="pbtuser", hashed_password="x", display_name="P")
                db.add(user)
                await db.flush()
                service = HealthService(db)
                await service.upsert_manual_day(user.id, DAY, dict(values))
                if not values:
                    return None
                return (await service.get_day(user.id, DAY)).values
        finally:
            await engine.dispose()

    result = asyncio.run(work())
    assert result == (values or None)


DAY = date(2026, 5, 20)
