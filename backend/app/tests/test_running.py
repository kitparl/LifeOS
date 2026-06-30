import pytest
from datetime import date


async def _auth_token(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "running@example.com", "password": "password123", "display_name": "Runner"},
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
            "run_date": "2026-06-30",
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
async def test_list_runs_and_race(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/running/runs",
        headers=headers,
        json={"run_date": "2026-06-28", "distance_km": 10.0, "duration_seconds": 3000},
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
