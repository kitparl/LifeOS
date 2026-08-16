from datetime import datetime, timedelta, timezone

import pytest


async def _auth_token(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
        "username": "routineuser","email": "routines@example.com", "password": "password123", "display_name": "Routine User"},
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
            "start_date": datetime.now(timezone.utc).date().isoformat(),
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
    assert body["blocks"][0]["habit_ids"] == []
    assert body["blocks"][1]["habit_ids"] == []
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


@pytest.mark.asyncio
async def test_routine_start_date_required(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/api/v1/routines",
        headers=headers,
        json={
            "name": "No start",
            "days_of_week": [0],
            "timezone": "UTC",
            "blocks": [
                {
                    "title": "X",
                    "start_time": "09:00:00",
                    "end_time": "10:00:00",
                }
            ],
        },
    )
    assert create.status_code == 422


@pytest.mark.asyncio
async def test_routine_list_sort_and_custom_taxonomy(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    today = datetime.now(timezone.utc).date()
    older = await client.post(
        "/api/v1/routines",
        headers=headers,
        json={
            "name": "Older",
            "days_of_week": [0],
            "timezone": "UTC",
            "start_date": (today - timedelta(days=20)).isoformat(),
            "end_date": (today + timedelta(days=1)).isoformat(),
            "blocks": [{"title": "A", "start_time": "09:00:00", "end_time": "10:00:00", "area": "yoga", "category": "wellness"}],
        },
    )
    newer = await client.post(
        "/api/v1/routines",
        headers=headers,
        json={
            "name": "Newer",
            "days_of_week": [0],
            "timezone": "UTC",
            "start_date": (today - timedelta(days=2)).isoformat(),
            "end_date": (today + timedelta(days=10)).isoformat(),
            "blocks": [{"title": "B", "start_time": "09:00:00", "end_time": "10:00:00"}],
        },
    )
    assert older.status_code == 201, older.text
    assert newer.status_code == 201, newer.text
    assert older.json()["blocks"][0]["area"] == "yoga"

    listing = await client.get("/api/v1/routines", headers=headers, params={"active_only": "false"})
    names = [r["name"] for r in listing.json()]
    assert names.index("Newer") < names.index("Older")

    areas = await client.get("/api/v1/routines/areas", headers=headers)
    assert "yoga" in areas.json()
    cats = await client.get("/api/v1/routines/categories", headers=headers)
    assert "wellness" in cats.json()


@pytest.mark.asyncio
async def test_expired_routine_saved_inactive(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    today = datetime.now(timezone.utc).date()
    create = await client.post(
        "/api/v1/routines",
        headers=headers,
        json={
            "name": "Past",
            "days_of_week": [0, 1, 2, 3, 4, 5, 6],
            "timezone": "UTC",
            "start_date": (today - timedelta(days=10)).isoformat(),
            "end_date": (today - timedelta(days=1)).isoformat(),
            "blocks": [{"title": "Old", "start_time": "09:00:00", "end_time": "10:00:00"}],
        },
    )
    assert create.status_code == 201, create.text
    assert create.json()["is_active"] is False


@pytest.mark.asyncio
async def test_routines_expire_job_registered():
    from app.modules.integrations import scheduler as sched_mod

    sched_mod.start_scheduler()
    try:
        assert sched_mod.get_scheduler().get_job("routines_expire") is not None
    finally:
        await sched_mod.shutdown_scheduler()


def test_period_is_outside_today():
    from datetime import date

    from app.modules.routines.expiry import period_is_outside_today

    today = date(2026, 8, 16)
    assert period_is_outside_today(date(2026, 1, 1), date(2026, 8, 1), today) is True
    assert period_is_outside_today(date(2026, 8, 1), date(2026, 8, 31), today) is False
    assert period_is_outside_today(date(2026, 9, 1), None, today) is False
    assert period_is_outside_today(None, date(2026, 8, 1), today) is True

