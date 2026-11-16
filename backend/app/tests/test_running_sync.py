"""Synced runs, manual-run matching, race attachment and AI/search exclusion (Unit 1: running-sync)."""

from datetime import date, datetime, timedelta, timezone

import pytest
from app.core.events import RUN_SYNCED, RUNS_IMPORTED, EntityCreated
from app.modules.ai.indexer import AiIndexer
from app.modules.auth.models import User
from app.modules.integrations.notifications.subscriber import format_entity_message, on_entity_created
from app.modules.notifications.models import Notification
from app.modules.running.contracts import SyncedRunInput
from app.modules.running.matching import local_run_date
from app.modules.running.service import RunningService
from app.modules.search.service import SearchService
from sqlalchemy import select

RUN_DAY = date(2026, 5, 3)
RUN_START = datetime(2026, 5, 3, 1, 0, tzinfo=timezone.utc)  # 06:30 in Asia/Kolkata, same local day


async def _register(client, name: str = "syncuser") -> tuple[dict, str]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": name,
            "email": f"{name}@example.com",
            "password": "password123",
            "display_name": "Runner",
        },
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    async with client.session_factory() as db:
        user = (await db.execute(select(User).where(User.username == name))).scalar_one()
    return headers, user.id


def _activity(activity_id: str = "act-1", *, km: float = 10.2, start: datetime = RUN_START) -> SyncedRunInput:
    return SyncedRunInput(
        activity_id=activity_id,
        source="garmin",
        start_time_utc=start,
        timezone="Asia/Kolkata",
        distance_m=km * 1000,
        timer_seconds=3120.4,
        elapsed_seconds=3300.0,
    )


async def _sync(client, user_id: str, data: SyncedRunInput):
    async with client.session_factory() as db:
        result = await RunningService(db).sync_run_from_activity(user_id, data)
        await db.commit()
    return result


async def _manual_run(client, headers, *, km: float = 10.0, day: date = RUN_DAY, notes: str = "Felt strong") -> dict:
    created = await client.post(
        "/api/v1/running/runs",
        headers=headers,
        json={
            "run_date": str(day),
            "distance_km": km,
            "duration_seconds": 3000,
            "weather": "cool",
            "shoe": "Pegasus",
            "notes": notes,
        },
    )
    assert created.status_code == 201
    return created.json()


async def _race(client, headers, *, day: date = RUN_DAY, **extra) -> dict:
    body = {"name": "City 10K", "race_date": str(day), "distance_type": "10k", "registered": True, **extra}
    created = await client.post("/api/v1/running/races", headers=headers, json=body)
    assert created.status_code == 201
    return created.json()


def test_local_run_date_uses_activity_timezone():
    late_utc = datetime(2026, 5, 2, 20, 0, tzinfo=timezone.utc)  # 01:30 on 3 May in Kolkata
    assert local_run_date(late_utc, "Asia/Kolkata") == date(2026, 5, 3)
    assert local_run_date(late_utc, None) == date(2026, 5, 2)
    assert local_run_date(late_utc, "Not/AZone") == date(2026, 5, 2)


@pytest.mark.asyncio
async def test_sync_creates_import_run_once(client):
    headers, user_id = await _register(client)

    first = await _sync(client, user_id, _activity())
    again = await _sync(client, user_id, _activity())

    assert first.created and not first.matched_manual
    assert again.run_id == first.run_id and not again.created

    runs = (await client.get("/api/v1/running/runs", headers=headers)).json()
    assert len(runs) == 1
    assert runs[0]["origin"] == "garmin"
    assert runs[0]["activity_id"] == "act-1"
    assert runs[0]["distance_km"] == 10.2
    assert runs[0]["duration_seconds"] == 3120
    assert runs[0]["run_date"] == str(RUN_DAY)

    detail = (await client.get(f"/api/v1/running/runs/{first.run_id}", headers=headers)).json()
    assert detail["elapsed_seconds"] == 3300


@pytest.mark.asyncio
async def test_activity_without_distance_or_time_is_not_a_run(client):
    headers, user_id = await _register(client)
    empty = SyncedRunInput("act-0", "garmin", RUN_START, None, 0.0, 600.0, 600.0)

    result = await _sync(client, user_id, empty)

    assert result.run_id is None
    assert (await client.get("/api/v1/running/runs", headers=headers)).json() == []


@pytest.mark.asyncio
async def test_matching_manual_run_keeps_user_fields_and_takes_synced_numbers(client):
    headers, user_id = await _register(client)
    manual = await _manual_run(client, headers)

    result = await _sync(client, user_id, _activity())

    assert result.run_id == manual["id"] and result.matched_manual and not result.created
    runs = (await client.get("/api/v1/running/runs", headers=headers)).json()
    assert len(runs) == 1
    merged = (await client.get(f"/api/v1/running/runs/{manual['id']}", headers=headers)).json()
    assert merged["notes"] == "Felt strong"
    assert merged["shoe"] == "Pegasus"
    assert merged["weather"] == "cool"
    assert merged["origin"] == "manual"
    assert merged["activity_id"] == "act-1"
    assert merged["distance_km"] == 10.2
    assert merged["duration_seconds"] == 3120


@pytest.mark.asyncio
async def test_manual_run_with_different_distance_is_not_matched(client):
    headers, user_id = await _register(client)
    await _manual_run(client, headers, km=5.0)

    result = await _sync(client, user_id, _activity())

    assert result.created
    assert len((await client.get("/api/v1/running/runs", headers=headers)).json()) == 2


@pytest.mark.asyncio
async def test_two_activities_match_at_most_one_manual_run(client):
    headers, user_id = await _register(client)
    manual = await _manual_run(client, headers)

    first = await _sync(client, user_id, _activity("act-1"))
    second = await _sync(client, user_id, _activity("act-2", km=10.1))

    assert first.run_id == manual["id"]
    assert second.created and second.run_id != manual["id"]
    assert len((await client.get("/api/v1/running/runs", headers=headers)).json()) == 2


@pytest.mark.asyncio
async def test_synced_fields_are_read_only_but_user_fields_are_editable(client):
    headers, user_id = await _register(client)
    run_id = (await _sync(client, user_id, _activity())).run_id

    patched = await client.patch(
        f"/api/v1/running/runs/{run_id}",
        headers=headers,
        json={"distance_km": 99.0, "duration_seconds": 60, "run_date": "2020-01-01", "notes": "Tempo", "shoe": "Vaporfly"},
    )

    assert patched.status_code == 200
    body = patched.json()
    assert body["distance_km"] == 10.2
    assert body["duration_seconds"] == 3120
    assert body["run_date"] == str(RUN_DAY)
    assert body["notes"] == "Tempo"
    assert body["shoe"] == "Vaporfly"


@pytest.mark.asyncio
async def test_manual_run_is_still_fully_editable(client):
    headers, _ = await _register(client)
    manual = await _manual_run(client, headers)

    patched = await client.patch(
        f"/api/v1/running/runs/{manual['id']}", headers=headers, json={"distance_km": 12.0}
    )

    assert patched.json()["distance_km"] == 12.0


@pytest.mark.asyncio
async def test_revert_deletes_import_runs_and_restores_matched_manual_runs(client):
    headers, user_id = await _register(client)
    manual = await _manual_run(client, headers)
    await _sync(client, user_id, _activity("act-1"))
    await _sync(client, user_id, _activity("act-2", km=6.0, start=RUN_START + timedelta(days=1)))

    async with client.session_factory() as db:
        result = await RunningService(db).revert_runs_for_activities(user_id, ["act-1", "act-2"])
        await db.commit()

    assert (result.runs_deleted, result.runs_restored) == (1, 1)
    runs = (await client.get("/api/v1/running/runs", headers=headers)).json()
    assert [r["id"] for r in runs] == [manual["id"]]
    restored = (await client.get(f"/api/v1/running/runs/{manual['id']}", headers=headers)).json()
    assert restored["distance_km"] == 10.0
    assert restored["duration_seconds"] == 3000
    assert restored["activity_id"] is None
    assert restored["notes"] == "Felt strong"


@pytest.mark.asyncio
async def test_race_candidates_are_synced_runs_within_three_days_closest_first(client):
    headers, user_id = await _register(client)
    race = await _race(client, headers)
    day_before = (await _sync(client, user_id, _activity("a-before", start=RUN_START - timedelta(days=1)))).run_id
    same_day = (await _sync(client, user_id, _activity("a-same"))).run_id
    await _sync(client, user_id, _activity("a-far", start=RUN_START + timedelta(days=8)))
    await _manual_run(client, headers, km=3.0)

    candidates = await client.get(f"/api/v1/running/races/{race['id']}/candidates", headers=headers)

    assert candidates.status_code == 200
    assert [c["id"] for c in candidates.json()] == [same_day, day_before]


@pytest.mark.asyncio
async def test_attach_sets_result_and_detach_restores_previous_values(client):
    headers, user_id = await _register(client)
    race = await _race(client, headers, finish_time_seconds=6730, bib_number="A12", medal=True, position=40)
    run_id = (await _sync(client, user_id, _activity())).run_id

    attached = await client.put(
        f"/api/v1/running/races/{race['id']}/attachment", headers=headers, json={"run_id": run_id}
    )

    assert attached.status_code == 200
    body = attached.json()
    assert body["run_id"] == run_id and body["activity_id"] == "act-1"
    assert body["finish_time_seconds"] == 3300
    assert body["attended"] is True
    assert (body["bib_number"], body["medal"], body["position"]) == ("A12", True, 40)

    detached = await client.delete(f"/api/v1/running/races/{race['id']}/attachment", headers=headers)

    assert detached.json()["run_id"] is None
    assert detached.json()["finish_time_seconds"] == 6730
    assert (await client.get(f"/api/v1/running/runs/{run_id}", headers=headers)).status_code == 200


@pytest.mark.asyncio
async def test_detach_restores_empty_finish_time_and_attendance(client):
    headers, user_id = await _register(client)
    race = await _race(client, headers)
    run_id = (await _sync(client, user_id, _activity())).run_id
    await client.put(f"/api/v1/running/races/{race['id']}/attachment", headers=headers, json={"run_id": run_id})

    detached = (await client.delete(f"/api/v1/running/races/{race['id']}/attachment", headers=headers)).json()

    assert detached["finish_time_seconds"] is None
    assert detached["attended"] is False


@pytest.mark.asyncio
async def test_one_run_per_race_and_one_race_per_run(client):
    headers, user_id = await _register(client)
    race = await _race(client, headers)
    other_race = await _race(client, headers, name="Other 10K")
    first = (await _sync(client, user_id, _activity("act-1"))).run_id
    second = (await _sync(client, user_id, _activity("act-2", km=10.0))).run_id
    await client.put(f"/api/v1/running/races/{race['id']}/attachment", headers=headers, json={"run_id": first})

    taken = await client.put(
        f"/api/v1/running/races/{other_race['id']}/attachment", headers=headers, json={"run_id": first}
    )
    offered = (await client.get(f"/api/v1/running/races/{other_race['id']}/candidates", headers=headers)).json()
    replaced = await client.put(
        f"/api/v1/running/races/{race['id']}/attachment", headers=headers, json={"run_id": second}
    )

    assert taken.status_code == 409
    assert [c["id"] for c in offered] == [second]
    assert replaced.json()["run_id"] == second
    assert (await client.get(f"/api/v1/running/runs/{first}", headers=headers)).json()["race_id"] is None


@pytest.mark.asyncio
async def test_manual_run_cannot_be_attached(client):
    headers, _ = await _register(client)
    race = await _race(client, headers)
    manual = await _manual_run(client, headers)

    response = await client.put(
        f"/api/v1/running/races/{race['id']}/attachment", headers=headers, json={"run_id": manual["id"]}
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_attached_run_and_race_are_counted_once(client):
    headers, user_id = await _register(client)
    today = date.today()
    start = datetime(today.year, today.month, today.day, 6, 0, tzinfo=timezone.utc)
    race = await _race(client, headers, day=today, shoe="Vaporfly")
    run_id = (await _sync(client, user_id, SyncedRunInput("act-1", "garmin", start, None, 10000.0, 2700.0, 2760.0))).run_id
    await client.patch(f"/api/v1/running/runs/{run_id}", headers=headers, json={"shoe": "Vaporfly"})
    await client.put(f"/api/v1/running/races/{race['id']}/attachment", headers=headers, json={"run_id": run_id})

    items = (await client.get("/api/v1/running/runs", headers=headers)).json()
    stats = (await client.get("/api/v1/running/stats", headers=headers)).json()

    assert len(items) == 1
    assert items[0]["source"] == "run" and items[0]["event_name"] == "City 10K" and items[0]["race_id"] == race["id"]
    assert stats["weekly_totals"][-1]["value"] == 10.0
    assert stats["shoe_totals"] == [
        {"shoe": "Vaporfly", "total_km": 10.0, "run_count": 1, "last_run_date": str(today)}
    ]
    assert stats["events_attended"] == 1


@pytest.mark.asyncio
async def test_deleting_an_attached_run_detaches_the_race(client):
    headers, user_id = await _register(client)
    race = await _race(client, headers, finish_time_seconds=3600)
    run_id = (await _sync(client, user_id, _activity())).run_id
    await client.put(f"/api/v1/running/races/{race['id']}/attachment", headers=headers, json={"run_id": run_id})

    deleted = await client.delete(f"/api/v1/running/runs/{run_id}", headers=headers)

    assert deleted.status_code == 204
    after = (await client.get(f"/api/v1/running/races/{race['id']}", headers=headers)).json()
    assert after["run_id"] is None and after["finish_time_seconds"] == 3600


@pytest.mark.asyncio
async def test_another_user_cannot_see_or_attach_my_runs_and_races(client):
    headers, user_id = await _register(client)
    race = await _race(client, headers)
    run_id = (await _sync(client, user_id, _activity())).run_id
    stranger, stranger_id = await _register(client, "stranger")
    stranger_race = await _race(client, stranger)

    assert (await client.get(f"/api/v1/running/races/{race['id']}/candidates", headers=stranger)).status_code == 404
    assert (await client.delete(f"/api/v1/running/races/{race['id']}/attachment", headers=stranger)).status_code == 404
    stolen = await client.put(
        f"/api/v1/running/races/{stranger_race['id']}/attachment", headers=stranger, json={"run_id": run_id}
    )
    assert stolen.status_code == 404
    assert (await client.get(f"/api/v1/running/races/{race['id']}/candidates")).status_code in (401, 403)

    async with client.session_factory() as db:
        result = await RunningService(db).revert_runs_for_activities(stranger_id, ["act-1"])
        await db.commit()
    assert result.runs_deleted == 0
    assert (await client.get(f"/api/v1/running/runs/{run_id}", headers=headers)).status_code == 200


@pytest.mark.asyncio
async def test_import_runs_stay_out_of_ai_index_and_search(client):
    headers, user_id = await _register(client)
    manual = await _manual_run(client, headers, notes="hilly tempo")
    await _sync(client, user_id, _activity("act-1"))  # merges into the manual run
    imported = (await _sync(client, user_id, _activity("act-2", km=7.0, start=RUN_START + timedelta(days=2)))).run_id
    await client.patch(f"/api/v1/running/runs/{imported}", headers=headers, json={"notes": "hilly recovery"})

    async with client.session_factory() as db:
        run_docs = [d for d in await AiIndexer(db).collect_documents(user_id) if d.source_type == "run"]
        found = await SearchService(db).search(user_id, "hilly")

    assert [d.source_id for d in run_docs] == [manual["id"]]
    assert run_docs[0].title == "Run 10.0km"  # the distance the user typed, not the synced 10.2
    run_hits = [r for r in found.results if r.entity_type == "run"]
    assert [r.id for r in run_hits] == [manual["id"]]
    assert run_hits[0].title == "10.0 km run"


def test_run_sync_messages():
    single = EntityCreated(RUN_SYNCED, "u1", "run-1", "10.2 km in 52:00 (5:06/km)", module="running")
    bulk = EntityCreated(RUNS_IMPORTED, "u1", "", "40 runs", module="running")

    assert format_entity_message(single) == "New run synced: 10.2 km in 52:00 (5:06/km)"
    assert format_entity_message(bulk) == "Runs imported: 40 runs"


@pytest.mark.asyncio
async def test_run_synced_event_creates_in_app_notification(client):
    _, user_id = await _register(client)

    async with client.session_factory() as db:
        await on_entity_created(db, EntityCreated(RUN_SYNCED, user_id, "run-1", "10.2 km in 52:00", module="running"))
        await db.commit()
        notes = (await db.execute(select(Notification).where(Notification.user_id == user_id))).scalars().all()

    assert [(n.message, n.module, n.route) for n in notes] == [
        ("New run synced: 10.2 km in 52:00", "running", "/running/run-1")
    ]
