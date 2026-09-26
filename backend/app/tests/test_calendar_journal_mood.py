from datetime import date, datetime, timedelta, timezone

import pytest


async def _auth_token(client, email="unit7@example.com"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
        "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),"email": email, "password": "password123", "display_name": "Unit7 User"},
    )
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_calendar_event_crud(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    starts = datetime.now(timezone.utc) + timedelta(days=1)

    create = await client.post(
        "/api/v1/calendar/events",
        headers=headers,
        json={"title": "Team standup", "starts_at": starts.isoformat(), "category": "task"},
    )
    assert create.status_code == 201
    event_id = create.json()["id"]

    listing = await client.get("/api/v1/calendar/events", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    delete = await client.delete(f"/api/v1/calendar/events/{event_id}", headers=headers)
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_journal_entry_create(client):
    token = await _auth_token(client, "journal@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/journal/entries",
        headers=headers,
        json={
            "entry_date": str(date.today()),
            "entry_type": "morning",
            "content": "Plan: finish Unit 7",
            "gratitude": "Good coffee",
        },
    )
    assert create.status_code == 201
    assert create.json()["entry_type"] == "morning"

    listing = await client.get("/api/v1/journal/entries", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


@pytest.mark.asyncio
async def test_mood_upsert_and_stats(client):
    token = await _auth_token(client, "mood@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    upsert = await client.put(
        "/api/v1/mood/today",
        headers=headers,
        json={"stress": 2, "confidence": 4, "motivation": 5, "happiness": 4},
    )
    assert upsert.status_code == 200

    today = await client.get("/api/v1/mood/today", headers=headers)
    assert today.status_code == 200
    assert today.json()["happiness"] == 4

    stats = await client.get("/api/v1/mood/stats", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["avg_happiness"] == 4.0
