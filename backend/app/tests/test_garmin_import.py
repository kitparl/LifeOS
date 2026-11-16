"""Garmin import through the API: upload, background job, idempotency, matching, failures, ownership, delete."""

import io
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from app.core.config import get_settings
from app.core.timezone import utc_now
from app.main import app
from app.modules.auth.models import User
from app.modules.integrations.garmin import import_service
from app.modules.integrations.garmin.api import get_session_factory
from app.modules.integrations.garmin.import_service import mark_interrupted_jobs, wait_for_imports
from app.modules.integrations.garmin.models import JOB_INTERRUPTED, JOB_RUNNING, GarminImportJob
from app.modules.integrations.notifications.subscriber import register_subscribers
from app.modules.notifications.models import Notification
from app.tests.fit_support import FitSpec, build_fit, steady_samples
from sqlalchemy import select

IMPORTS = "/api/v1/integrations/garmin/imports"


def _when(days_ago: int) -> datetime:
    return (utc_now() - timedelta(days=days_ago)).replace(hour=6, minute=0, second=0, microsecond=0)


def fit(serial: int = 1001, *, days_ago: int = 20, km: float = 10.2, sport: int = 1, **spec) -> bytes:
    timer = km * 306.0  # about 5:06 per km
    return build_fit(
        FitSpec(
            start=_when(days_ago),
            serial=serial,
            sport=sport,
            distance_m=km * 1000,
            timer_s=timer,
            elapsed_s=timer + 60,
            samples=steady_samples(km * 1000, timer, count=int(km * 10)),
            laps=2,
            **spec,
        )
    )


def zip_of(entries: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return buffer.getvalue()


@pytest.fixture
async def api(client):
    """Client whose background imports use the test database."""
    app.dependency_overrides[get_session_factory] = lambda: client.session_factory
    register_subscribers()  # normally done by the app's startup, which the test client skips
    return client


async def register(client, name: str = "garminuser") -> tuple[dict, str]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": name, "email": f"{name}@example.com", "password": "password123", "display_name": "G"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    async with client.session_factory() as db:
        user_id = (await db.execute(select(User.id).where(User.username == name))).scalar_one()
    return headers, user_id


async def upload(client, headers, files: dict[str, bytes], **form):
    parts = [("files", (name, data, "application/octet-stream")) for name, data in files.items()]
    return await client.post(IMPORTS, headers=headers, files=parts, data=form)


async def run_import(client, headers, files: dict[str, bytes], **form) -> dict:
    response = await upload(client, headers, files, **form)
    assert response.status_code == 202, response.text
    await wait_for_imports()
    job = await client.get(f"{IMPORTS}/{response.json()['id']}", headers=headers)
    return job.json()


async def runs_of(client, headers) -> list[dict]:
    return (await client.get("/api/v1/running/runs", headers=headers)).json()


@pytest.mark.asyncio
async def test_single_fit_import_creates_run_activity_series_and_original(api):
    headers, user_id = await register(api)

    job = await run_import(api, headers, {"morning.fit": fit()})

    assert (job["status"], job["files_found"], job["created"], job["failed"]) == ("finished", 1, 1, 0)
    assert (job["runs_created"], job["runs_matched"], job["errors"]) == (1, 0, [])
    assert job["started_at"] and job["finished_at"]

    runs = await runs_of(api, headers)
    assert len(runs) == 1 and runs[0]["origin"] == "garmin" and runs[0]["distance_km"] == 10.2
    activity_id = runs[0]["activity_id"]

    detail = (await api.get(f"/api/v1/activities/{activity_id}", headers=headers)).json()
    assert detail["sport"] == "running" and detail["has_route"] and detail["has_series"] and detail["has_original_file"]
    assert len(detail["splits"]) == 11 and detail["splits"][0]["distance_m"] == 1000.0
    assert len(detail["laps"]) == 2 and detail["training_effect_aerobic"] == 3.4

    series = (await api.get(f"/api/v1/activities/{activity_id}/series", headers=headers)).json()
    assert series["sample_count"] == 103 and series["route"] and series["heart_rate"]

    files = (await api.get("/api/v1/files", headers=headers, params={"module": "running"})).json()
    items = files["items"] if isinstance(files, dict) else files
    assert [f["filename"] for f in items] == ["morning.fit"]


@pytest.mark.asyncio
async def test_reimporting_the_same_file_changes_nothing(api):
    headers, _ = await register(api)
    data = fit()
    await run_import(api, headers, {"a.fit": data})
    before = await runs_of(api, headers)

    again = await run_import(api, headers, {"renamed.fit": data})

    assert (again["created"], again["duplicates"], again["runs_created"]) == (0, 1, 0)
    assert await runs_of(api, headers) == before


@pytest.mark.asyncio
async def test_archive_import_applies_the_twelve_month_range_by_default(api):
    headers, _ = await register(api)
    archive = zip_of(
        {
            "DI_CONNECT/a.fit": fit(1, days_ago=10),
            "DI_CONNECT/b.fit": fit(2, days_ago=100, km=5.0),
            "DI_CONNECT/old.fit": fit(3, days_ago=800, km=8.0),
            "readme.txt": b"not a fit",
        }
    )

    default = await run_import(api, headers, {"export.zip": archive})
    everything = await run_import(api, headers, {"export.zip": archive}, range="all")

    assert (default["files_found"], default["created"], default["outside_range"]) == (3, 2, 1)
    assert (everything["created"], everything["duplicates"], everything["outside_range"]) == (1, 2, 0)
    assert len(await runs_of(api, headers)) == 3


@pytest.mark.asyncio
async def test_nested_archives_like_a_real_garmin_export_are_read(api):
    headers, _ = await register(api)
    inner = zip_of({"run1.fit": fit(11), "run2.fit": fit(12, days_ago=21, km=6.0)})
    export = zip_of({"DI_CONNECT/DI-Connect-Uploaded-Files/UploadedFiles_0-_Part1.zip": inner})

    job = await run_import(api, headers, {"export.zip": export})

    assert (job["files_found"], job["created"], job["runs_created"]) == (2, 2, 2)


@pytest.mark.asyncio
async def test_a_damaged_file_does_not_stop_the_rest_and_is_reported_plainly(api):
    headers, _ = await register(api)
    good = fit(21)
    broken = bytearray(fit(22, days_ago=21))
    broken[60] ^= 0xFF
    archive = zip_of({"../../etc/ok.fit": good, "bad.fit": bytes(broken), "../x/short.fit": fit(23)[:40]})

    job = await run_import(api, headers, {"export.zip": archive})

    assert (job["status"], job["created"], job["failed"]) == ("finished", 1, 2)
    assert {e["name"] for e in job["errors"]} == {"bad.fit", "short.fit"}
    assert {e["reason"] for e in job["errors"]} == {"File is damaged or incomplete"}
    assert "/" not in "".join(e["name"] for e in job["errors"])


@pytest.mark.asyncio
async def test_a_top_level_fit_with_a_bad_body_is_a_failed_file_not_a_rejected_request(api):
    headers, _ = await register(api)
    broken = bytearray(fit(31))
    broken[70] ^= 0xFF

    job = await run_import(api, headers, {"bad.fit": bytes(broken)})

    assert (job["status"], job["created"], job["failed"]) == ("finished", 0, 1)


@pytest.mark.asyncio
async def test_files_that_are_not_activities_are_counted_not_failed(api):
    headers, _ = await register(api)

    job = await run_import(api, headers, {"settings.fit": fit(41, file_type=2), "run.fit": fit(42)})

    assert (job["files_found"], job["not_activity"], job["created"], job["failed"]) == (2, 1, 1, 0)


@pytest.mark.asyncio
async def test_other_sports_are_stored_but_make_no_run(api):
    headers, _ = await register(api)

    job = await run_import(api, headers, {"ride.fit": fit(51, km=30.0, sport=2)})

    assert (job["created"], job["runs_created"]) == (1, 0)
    assert await runs_of(api, headers) == []
    summary = (await api.get("/api/v1/integrations/garmin/data/summary", headers=headers)).json()
    assert summary == {"activities": 1, "runs_created": 0, "runs_merged_into_manual": 0, "health_days": 0}


@pytest.mark.asyncio
async def test_import_merges_into_a_manual_run_and_delete_restores_it(api):
    headers, user_id = await register(api)
    start = _when(20)
    manual = (
        await api.post(
            "/api/v1/running/runs",
            headers=headers,
            json={
                "run_date": str(start.date()),
                "distance_km": 10.0,
                "duration_seconds": 3000,
                "notes": "Felt strong",
                "shoe": "Pegasus",
            },
        )
    ).json()

    job = await run_import(api, headers, {"a.fit": fit(61), "b.fit": fit(62, days_ago=19, km=5.0)})

    assert (job["created"], job["runs_created"], job["runs_matched"]) == (2, 1, 1)
    merged = (await api.get(f"/api/v1/running/runs/{manual['id']}", headers=headers)).json()
    assert (merged["notes"], merged["shoe"], merged["distance_km"]) == ("Felt strong", "Pegasus", 10.2)
    summary = (await api.get("/api/v1/integrations/garmin/data/summary", headers=headers)).json()
    assert summary == {"activities": 2, "runs_created": 1, "runs_merged_into_manual": 1, "health_days": 0}

    deleted = await api.delete("/api/v1/integrations/garmin/data", headers=headers)

    assert deleted.status_code == 200
    assert deleted.json() == {
        "activities_deleted": 2, "runs_deleted": 1, "runs_restored": 1, "races_detached": 0, "files_deleted": 2,
        "health_days_deleted": 0,
    }
    remaining = await runs_of(api, headers)
    assert [r["id"] for r in remaining] == [manual["id"]]
    assert (remaining[0]["distance_km"], remaining[0]["duration_seconds"], remaining[0]["activity_id"]) == (10.0, 3000, None)
    assert (await api.get(f"/api/v1/activities/{merged['activity_id']}", headers=headers)).status_code == 404
    log = (await api.get(IMPORTS, headers=headers)).json()
    assert len(log) == 1  # the sync log is kept
    assert (await api.get("/api/v1/integrations/garmin/data/summary", headers=headers)).json()["activities"] == 0
    # re-import after delete brings everything back
    again = await run_import(api, headers, {"a.fit": fit(61)})
    assert again["created"] == 1


@pytest.mark.asyncio
async def test_synced_run_can_be_attached_to_a_race_and_survives_the_full_journey(api):
    headers, _ = await register(api)
    race_day = _when(20).date()
    race = (
        await api.post(
            "/api/v1/running/races",
            headers=headers,
            json={"name": "City 10K", "race_date": str(race_day), "distance_type": "10k", "registered": True},
        )
    ).json()
    await run_import(api, headers, {"a.fit": fit(71)})
    run_id = (await runs_of(api, headers))[0]["id"]

    candidates = (await api.get(f"/api/v1/running/races/{race['id']}/candidates", headers=headers)).json()
    attached = await api.put(
        f"/api/v1/running/races/{race['id']}/attachment", headers=headers, json={"run_id": run_id}
    )

    assert [c["id"] for c in candidates] == [run_id]
    assert attached.json()["finish_time_seconds"] == round(10.2 * 306.0) + 60
    assert attached.json()["activity_id"]


@pytest.mark.asyncio
async def test_notifications_one_for_a_single_run_one_summary_for_many(api):
    headers, user_id = await register(api)

    await run_import(api, headers, {"a.fit": fit(81)})
    await run_import(api, headers, {"b.fit": fit(82, days_ago=19, km=5.0), "c.fit": fit(83, days_ago=18, km=6.0)})
    await run_import(api, headers, {"b.fit": fit(82, days_ago=19, km=5.0)})  # nothing new

    async with api.session_factory() as db:
        rows = (await db.execute(select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at))).scalars().all()
    assert [(n.message, n.module) for n in rows] == [
        ("New run synced: 10.2 km in 52:01 (5:06/km)", "running"),
        ("Runs imported: 2 runs", "running"),
    ]
    assert rows[0].route.startswith("/running/")


@pytest.mark.asyncio
async def test_unsupported_oversized_and_too_many_files_are_rejected_before_any_job(api, monkeypatch):
    headers, user_id = await register(api)
    settings = get_settings()

    text = await upload(api, headers, {"notes.fit": b"this is plain text, not a FIT file"})
    monkeypatch.setattr(settings, "garmin_import_max_fit_bytes", 100)
    big = await upload(api, headers, {"big.fit": fit(91)})
    monkeypatch.undo()
    monkeypatch.setattr(settings, "garmin_import_max_files", 1)
    many = await upload(api, headers, {"a.fit": fit(92), "b.fit": fit(93)})
    nothing = await api.post(IMPORTS, headers=headers, data={"range": "12m"})
    bad_range = await upload(api, headers, {"a.fit": fit(94)}, range="forever")

    assert text.status_code == 400 and "Unsupported file type" in text.json()["detail"]
    assert big.status_code == 413 and "limit" in big.json()["detail"]
    assert many.status_code == 400
    assert nothing.status_code == 422
    assert bad_range.status_code == 422
    async with api.session_factory() as db:
        assert (await db.execute(select(GarminImportJob))).scalars().all() == []
    assert await runs_of(api, headers) == []


@pytest.mark.asyncio
async def test_only_one_import_runs_at_a_time(api):
    headers, user_id = await register(api)
    async with api.session_factory() as db:
        db.add(GarminImportJob(user_id=user_id, status=JOB_RUNNING))
        await db.commit()

    response = await upload(api, headers, {"a.fit": fit(101)})

    assert response.status_code == 409
    assert await runs_of(api, headers) == []


@pytest.mark.asyncio
async def test_unfinished_jobs_are_marked_interrupted_at_startup(api):
    _, user_id = await register(api)
    async with api.session_factory() as db:
        db.add(GarminImportJob(user_id=user_id, status=JOB_RUNNING))
        await db.commit()

    assert await mark_interrupted_jobs(api.session_factory) == 1

    async with api.session_factory() as db:
        job = (await db.execute(select(GarminImportJob))).scalar_one()
    assert job.status == JOB_INTERRUPTED and job.finished_at is not None


@pytest.mark.asyncio
async def test_archive_limits_are_reported_as_failed_files_with_fixed_reasons(api, monkeypatch):
    headers, _ = await register(api)
    settings = get_settings()
    archive = zip_of({"a.fit": fit(111), "b.fit": fit(112, days_ago=21)})

    monkeypatch.setattr(settings, "garmin_import_max_entry_bytes", 1000)
    oversize = await run_import(api, headers, {"e.zip": archive})
    monkeypatch.undo()
    monkeypatch.setattr(settings, "garmin_import_max_archive_entries", 1)
    crowded = await run_import(api, headers, {"e.zip": archive})
    monkeypatch.undo()
    monkeypatch.setattr(settings, "fit_parse_max_messages", 5)
    capped = await run_import(api, headers, {"a.fit": fit(113)})

    assert {e["reason"] for e in oversize["errors"]} == {"File is too large to process"} and oversize["failed"] == 2
    assert [e["reason"] for e in crowded["errors"]] == ["Archive has too many files"]
    assert [e["reason"] for e in capped["errors"]] == ["File is too large to process"]
    assert await runs_of(api, headers) == []


@pytest.mark.asyncio
async def test_temp_files_are_removed_on_success_failure_and_rejection(api, monkeypatch):
    headers, _ = await register(api)
    created: list[Path] = []
    real_mkdtemp = import_service.tempfile.mkdtemp

    def recording_mkdtemp(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(Path(path))
        return path

    monkeypatch.setattr(import_service.tempfile, "mkdtemp", recording_mkdtemp)

    await run_import(api, headers, {"a.fit": fit(121)})
    await upload(api, headers, {"notes.fit": b"plain text, definitely not fit"})
    broken = bytearray(fit(122))
    broken[70] ^= 0xFF
    await run_import(api, headers, {"b.fit": bytes(broken)})

    assert len(created) == 3
    assert not any(path.exists() for path in created)


@pytest.mark.asyncio
async def test_sync_log_lists_every_import_newest_first_and_never_purges(api):
    headers, _ = await register(api)
    for serial in (131, 132, 133):
        await run_import(api, headers, {"a.fit": fit(serial, days_ago=serial - 100)})

    response = await api.get(IMPORTS, headers=headers, params={"limit": 2})

    assert response.headers["X-Total-Count"] == "3"
    assert len(response.json()) == 2
    created = [j["created_at"] for j in response.json()]
    assert created == sorted(created, reverse=True)


@pytest.mark.asyncio
async def test_another_user_cannot_read_my_imports_activities_or_series(api):
    headers, _ = await register(api)
    job = await run_import(api, headers, {"a.fit": fit(141)})
    activity_id = (await runs_of(api, headers))[0]["activity_id"]
    stranger, _ = await register(api, "stranger")

    for path in (
        f"{IMPORTS}/{job['id']}",
        f"/api/v1/activities/{activity_id}",
        f"/api/v1/activities/{activity_id}/series",
    ):
        assert (await api.get(path, headers=stranger)).status_code == 404
        assert (await api.get(path)).status_code in (401, 403)
    assert (await api.get(IMPORTS, headers=stranger)).json() == []
    assert (await api.delete("/api/v1/integrations/garmin/data", headers=stranger)).json()["activities_deleted"] == 0
    assert (await api.get(f"/api/v1/activities/{activity_id}", headers=headers)).status_code == 200


@pytest.mark.asyncio
async def test_activity_without_samples_has_detail_but_no_series(api):
    headers, _ = await register(api)
    summary_only = build_fit(FitSpec(start=_when(20), serial=151, distance_m=5000.0, timer_s=1500.0, elapsed_s=1500.0))

    await run_import(api, headers, {"a.fit": summary_only})
    run = (await runs_of(api, headers))[0]

    detail = (await api.get(f"/api/v1/activities/{run['activity_id']}", headers=headers)).json()
    assert (detail["has_series"], detail["has_route"], detail["splits"]) == (False, False, [])
    assert (await api.get(f"/api/v1/activities/{run['activity_id']}/series", headers=headers)).status_code == 404

