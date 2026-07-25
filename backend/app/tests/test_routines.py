from datetime import datetime, timedelta, timezone

import pytest


async def _auth_token(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "routines@example.com", "password": "password123", "display_name": "Routine User"},
    )
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_routine_crud_and_calendar_expansion(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/routines",
        headers=headers,
        json={
            "name": "Weekday Focus",
            "days_of_week": [0, 1, 2, 3, 4, 5, 6],
            "timezone": "UTC",
            "blocks": [
                {
                    "title": "DSA",
                    "start_time": "08:00:00",
                    "end_time": "10:00:00",
                    "area": "dsa",
                    "category": "learning",
                    "sort_order": 0,
                },
                {
                    "title": "Gym",
                    "start_time": "18:00:00",
                    "end_time": "19:00:00",
                    "area": "gym",
                    "category": "personal",
                    "sort_order": 1,
                },
            ],
        },
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["name"] == "Weekday Focus"
    assert len(body["blocks"]) == 2
    routine_id = body["id"]

    listing = await client.get("/api/v1/routines", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["block_count"] == 2

    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=2)
    cal = await client.get(
        "/api/v1/calendar/events",
        headers=headers,
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    assert cal.status_code == 200
    titles = {e["title"] for e in cal.json()}
    assert "DSA" in titles
    assert "Gym" in titles
    assert all(e.get("source_module") == "routine" for e in cal.json() if e["title"] in {"DSA", "Gym"})

    detail = await client.get(f"/api/v1/routines/{routine_id}", headers=headers)
    assert detail.status_code == 200

    delete = await client.delete(f"/api/v1/routines/{routine_id}", headers=headers)
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_routine_period_and_skip_dates(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    today = datetime.now(timezone.utc).date()
    skip = today.isoformat()
    create = await client.post(
        "/api/v1/routines",
        headers=headers,
        json={
            "name": "Bounded",
            "days_of_week": [0, 1, 2, 3, 4, 5, 6],
            "timezone": "UTC",
            "start_date": (today - timedelta(days=1)).isoformat(),
            "end_date": (today + timedelta(days=1)).isoformat(),
            "skip_dates": [skip],
            "blocks": [
                {
                    "title": "Focus",
                    "start_time": "09:00:00",
                    "end_time": "10:00:00",
                    "area": "learning",
                    "category": "learning",
                }
            ],
        },
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["start_date"] == (today - timedelta(days=1)).isoformat()
    assert skip in body["skip_dates"]

    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    cal = await client.get(
        "/api/v1/calendar/events",
        headers=headers,
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    assert cal.status_code == 200
    # Skipped today — no Focus block for today
    today_focus = [
        e
        for e in cal.json()
        if e["title"] == "Focus" and e["id"].endswith(skip)
    ]
    assert today_focus == []

    # Outside period: far future should have no blocks
    far_start = start + timedelta(days=30)
    far_end = far_start + timedelta(days=1)
    cal2 = await client.get(
        "/api/v1/calendar/events",
        headers=headers,
        params={"start": far_start.isoformat(), "end": far_end.isoformat()},
    )
    assert cal2.status_code == 200
    assert not any(e["title"] == "Focus" for e in cal2.json())
