from datetime import date, datetime, timedelta, timezone

import pytest


async def _headers(client, email="timeline@example.com"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "usr_" + email.split("@")[0].replace(".", "").replace("-", ""),
            "email": email,
            "password": "password123",
            "display_name": "Timeline User",
        },
    )
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def _window(days: int = 30) -> dict[str, str]:
    today = date.today()
    return {"start": str(today - timedelta(days=days)), "end": str(today + timedelta(days=days))}


@pytest.mark.asyncio
async def test_timeline_sources_lists_registry(client):
    headers = await _headers(client)
    resp = await client.get("/api/v1/timeline/sources", headers=headers)
    assert resp.status_code == 200
    by_key = {s["key"]: s for s in resp.json()}
    assert by_key["calendar"]["default_enabled"] is True
    assert by_key["routines"]["default_enabled"] is False


@pytest.mark.asyncio
async def test_timeline_merges_sources_in_chronological_order(client):
    headers = await _headers(client)
    today = date.today()
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)

    await client.post(
        "/api/v1/calendar/events",
        headers=headers,
        json={"title": "Dentist", "starts_at": tomorrow.isoformat(), "category": "personal"},
    )
    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "File taxes", "due_date": (tomorrow + timedelta(days=2)).isoformat()},
    )
    await client.post(
        "/api/v1/running/runs",
        headers=headers,
        json={"run_date": str(today - timedelta(days=3)), "distance_km": 5.0, "duration_seconds": 1800},
    )
    race = await client.post(
        "/api/v1/running/races",
        headers=headers,
        json={"name": "City 10K", "race_date": str(today + timedelta(days=10)), "distance_type": "10k"},
    )

    resp = await client.get("/api/v1/timeline", headers=headers, params=_window())
    assert resp.status_code == 200
    items = resp.json()
    titles = [i["title"] for i in items]
    assert titles == ["5 km run", "Dentist", "File taxes", "City 10K"]

    race_item = items[-1]
    # Calendar-mirrored races are attributed to Running and link to the race page.
    assert race_item["source"] == "running"
    assert race_item["route"] == f"/running/races/{race.json()['id']}"
    assert items[0]["all_day"] is True


@pytest.mark.asyncio
async def test_timeline_filters_by_sources(client):
    headers = await _headers(client, "timeline-filter@example.com")
    today = date.today()
    await client.post(
        "/api/v1/running/races",
        headers=headers,
        json={"name": "Half", "race_date": str(today + timedelta(days=5)), "distance_type": "half"},
    )
    await client.post(
        "/api/v1/calendar/events",
        headers=headers,
        json={"title": "Lunch", "starts_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
    )

    resp = await client.get(
        "/api/v1/timeline", headers=headers, params={**_window(), "sources": ["calendar"]}
    )
    assert resp.status_code == 200
    assert [i["title"] for i in resp.json()] == ["Lunch"]


@pytest.mark.asyncio
async def test_timeline_rejects_bad_input(client):
    headers = await _headers(client, "timeline-bad@example.com")
    today = date.today()

    reversed_window = await client.get(
        "/api/v1/timeline",
        headers=headers,
        params={"start": str(today), "end": str(today - timedelta(days=1))},
    )
    assert reversed_window.status_code == 400

    too_wide = await client.get(
        "/api/v1/timeline",
        headers=headers,
        params={"start": str(today), "end": str(today + timedelta(days=400))},
    )
    assert too_wide.status_code == 400

    unknown = await client.get(
        "/api/v1/timeline", headers=headers, params={**_window(), "sources": ["nope"]}
    )
    assert unknown.status_code == 400
