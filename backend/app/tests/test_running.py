import pytest
from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.modules.running.service import RunningService


async def _auth_token(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
        "username": "runuser","email": "running@example.com", "password": "password123", "display_name": "Runner"},
    )
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_create_run_and_stats(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/running/runs",
        headers=headers,
        json={
            "run_date": str(date.today()),
            "distance_km": 5.0,
            "duration_seconds": 1500,
            "weather": "sunny",
            "notes": "Easy 5K",
        },
    )
    assert create.status_code == 201
    data = create.json()
    assert data["distance_km"] == 5.0
    assert data["pace_min_per_km"] == 5.0

    stats = await client.get("/api/v1/running/stats", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["total_runs"] == 1
    assert stats.json()["weekly_km"] == 5.0
    pb = stats.json()["personal_bests"]
    five_k = next(b for b in pb if b["distance_type"] == "5k")
    assert five_k["pace_min_per_km"] == 5.0


@pytest.mark.asyncio
async def test_run_shoes_and_totals(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    shoes = await client.get("/api/v1/running/shoes", headers=headers)
    assert shoes.status_code == 200
    assert "Daily trainer" in shoes.json()

    created = await client.post(
        "/api/v1/running/shoes",
        headers=headers,
        json={"name": "Pegasus"},
    )
    assert created.status_code == 201
    assert "Pegasus" in created.json()

    run = await client.post(
        "/api/v1/running/runs",
        headers=headers,
        json={
            "run_date": str(date.today()),
            "distance_km": 8.0,
            "duration_seconds": 2400,
            "shoe": "Pegasus",
        },
    )
    assert run.status_code == 201
    assert run.json()["shoe"] == "Pegasus"

    filtered = await client.get("/api/v1/running/runs", headers=headers, params={"shoe": "Pegasus"})
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    stats = await client.get("/api/v1/running/stats", headers=headers)
    assert stats.status_code == 200
    totals = stats.json()["shoe_totals"]
    peg = next(t for t in totals if t["shoe"] == "Pegasus")
    assert peg["total_km"] == 8.0
    assert peg["run_count"] == 1


@pytest.mark.asyncio
async def test_race_shoes_in_totals(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    race = await client.post(
        "/api/v1/running/races",
        headers=headers,
        json={
            "name": "City 10K",
            "race_date": "2026-07-01",
            "distance_type": "10k",
            "shoe": "Race day Vapor",
            "attended": True,
            "finish_time_seconds": 2700,
        },
    )
    assert race.status_code == 201
    assert race.json()["shoe"] == "Race day Vapor"

    shoes = await client.get("/api/v1/running/shoes", headers=headers)
    assert "Race day Vapor" in shoes.json()

    stats = await client.get("/api/v1/running/stats", headers=headers)
    assert stats.status_code == 200
    totals = stats.json()["shoe_totals"]
    vapor = next(t for t in totals if t["shoe"] == "Race day Vapor")
    assert vapor["total_km"] == 10.0
    assert vapor["run_count"] == 1


@pytest.mark.asyncio
async def test_list_runs_and_race(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/running/runs",
        headers=headers,
        json={"run_date": str(date.today()), "distance_km": 10.0, "duration_seconds": 3000},
    )

    race = await client.post(
        "/api/v1/running/races",
        headers=headers,
        json={
            "name": "City Marathon",
            "race_date": "2026-12-01",
            "distance_type": "marathon",
            "registered": True,
        },
    )
    assert race.status_code == 201

    runs = await client.get("/api/v1/running/runs", headers=headers)
    assert runs.status_code == 200
    assert len(runs.json()) == 1

    races = await client.get("/api/v1/running/races", headers=headers)
    assert races.status_code == 200
    assert races.json()[0]["name"] == "City Marathon"


@pytest.mark.asyncio
async def test_create_race_get_by_id_past_event(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/running/races",
        headers=headers,
        json={
            "name": "Yesterday Marathon",
            "race_date": "2026-07-05",
            "distance_type": "marathon",
            "attended": True,
            "finish_time_seconds": 14400,
        },
    )
    assert create.status_code == 201
    race_id = create.json()["id"]
    assert create.json()["attended"] is True

    get = await client.get(f"/api/v1/running/races/{race_id}", headers=headers)
    assert get.status_code == 200
    assert get.json()["name"] == "Yesterday Marathon"
    assert get.json()["finish_time_seconds"] == 14400


def test_race_response_handles_legacy_nulls_and_string_photos():
    now = datetime.now(timezone.utc)
    race = SimpleNamespace(
        id="legacy-race",
        name="Legacy Race",
        race_date=date(2026, 1, 1),
        distance_type="10k",
        distance_km=None,
        location=None,
        organizer=None,
        bib_number=None,
        finish_time_seconds=None,
        position=None,
        medal=None,
        certificate_url=None,
        event_url=None,
        photos='["https://example.com/photo.jpg"]',
        registered=None,
        attended=None,
        notes=None,
        created_at=now,
        updated_at=now,
    )

    response = RunningService._to_race_response(race)

    assert response.registered is False
    assert response.attended is False
    assert response.medal is False
    assert response.photos == ["https://example.com/photo.jpg"]


@pytest.mark.asyncio
async def test_dashboard_running_progress(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.patch(
        "/api/v1/running/settings",
        headers=headers,
        json={"weekly_goal_km": 50},
    )
    await client.post(
        "/api/v1/running/runs",
        headers=headers,
        json={"run_date": str(date.today()), "distance_km": 8.0, "duration_seconds": 2880},
    )

    summary = await client.get("/api/v1/dashboard/summary", headers=headers)
    progress = summary.json()["running_progress"]
    assert progress is not None
    assert progress["weekly_km"] == 8.0
    assert progress["goal_km"] == 50.0
