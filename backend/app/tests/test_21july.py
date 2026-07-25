import pytest


async def _auth_token(client, email):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "July User"},
    )
    return reg.json()["access_token"]


# =========================================================
# Running <-> Calendar two-way sync
# =========================================================


@pytest.mark.asyncio
async def test_race_creates_and_updates_calendar_event(client):
    token = await _auth_token(client, "sync1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    race = await client.post(
        "/api/v1/running/races",
        headers=headers,
        json={"name": "City Marathon", "race_date": "2026-12-01", "distance_type": "marathon"},
    )
    assert race.status_code == 201
    race_id = race.json()["id"]

    events = await client.get("/api/v1/calendar/events", headers=headers)
    assert events.status_code == 200
    linked = [e for e in events.json() if e.get("source_module") == "running"]
    assert len(linked) == 1
    assert linked[0]["title"] == "City Marathon"
    assert linked[0]["category"] == "running"
    assert linked[0]["all_day"] is True
    assert linked[0]["source_id"] == race_id

    # Updating the race updates the same calendar event (no duplicate).
    await client.patch(
        f"/api/v1/running/races/{race_id}",
        headers=headers,
        json={"name": "City Marathon (Elite)"},
    )
    events = await client.get("/api/v1/calendar/events", headers=headers)
    linked = [e for e in events.json() if e.get("source_module") == "running"]
    assert len(linked) == 1
    assert linked[0]["title"] == "City Marathon (Elite)"


@pytest.mark.asyncio
async def test_race_delete_removes_calendar_event(client):
    token = await _auth_token(client, "sync2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    race = await client.post(
        "/api/v1/running/races",
        headers=headers,
        json={"name": "10K Run", "race_date": "2026-10-10", "distance_type": "10k"},
    )
    race_id = race.json()["id"]

    await client.delete(f"/api/v1/running/races/{race_id}", headers=headers)

    events = await client.get("/api/v1/calendar/events", headers=headers)
    linked = [e for e in events.json() if e.get("source_module") == "running"]
    assert linked == []


@pytest.mark.asyncio
async def test_calendar_edit_propagates_back_to_race(client):
    token = await _auth_token(client, "sync3@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    race = await client.post(
        "/api/v1/running/races",
        headers=headers,
        json={"name": "Trail Race", "race_date": "2026-09-01", "distance_type": "half_marathon"},
    )
    race_id = race.json()["id"]

    events = await client.get("/api/v1/calendar/events", headers=headers)
    event_id = next(e["id"] for e in events.json() if e.get("source_id") == race_id)

    # Edit the linked calendar event -> race reflects new title + date.
    await client.patch(
        f"/api/v1/calendar/events/{event_id}",
        headers=headers,
        json={"title": "Trail Race Rescheduled", "starts_at": "2027-01-15T00:00:00+00:00"},
    )

    race_after = await client.get(f"/api/v1/running/races/{race_id}", headers=headers)
    assert race_after.json()["name"] == "Trail Race Rescheduled"
    assert race_after.json()["race_date"] == "2027-01-15"

    # Deleting the linked calendar event deletes the race too.
    await client.delete(f"/api/v1/calendar/events/{event_id}", headers=headers)
    gone = await client.get(f"/api/v1/running/races/{race_id}", headers=headers)
    assert gone.status_code == 404


# =========================================================
# Q&A extensible Type field
# =========================================================


@pytest.mark.asyncio
async def test_qa_types_suggested_and_custom(client):
    token = await _auth_token(client, "qatypes@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    types = await client.get("/api/v1/qa/types", headers=headers)
    assert types.status_code == 200
    assert "Tech" in types.json()
    assert "Learning" in types.json()

    created = await client.post(
        "/api/v1/qa/entries",
        headers=headers,
        json={"question": "STAR method?", "answer": "Situation, Task, Action, Result", "type": "Interview"},
    )
    assert created.status_code == 201
    assert created.json()["type"] == "Interview"

    # Custom type is now registered and reusable.
    types = await client.get("/api/v1/qa/types", headers=headers)
    assert "Interview" in types.json()

    # Filter by type.
    filtered = await client.get("/api/v1/qa/entries?type=Interview", headers=headers)
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["type"] == "Interview"


@pytest.mark.asyncio
async def test_qa_create_type_endpoint(client):
    token = await _auth_token(client, "qatypes2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/qa/types", headers=headers, json={"name": "Finance"})
    assert resp.status_code == 201
    assert "Finance" in resp.json()


# =========================================================
# Wishlist / Goals extensible categories
# =========================================================


@pytest.mark.asyncio
async def test_wishlist_categories_suggested_and_custom(client):
    token = await _auth_token(client, "wishcats@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    cats = await client.get("/api/v1/wishlist/categories", headers=headers)
    assert cats.status_code == 200
    assert "travel" in cats.json()
    assert "other" in cats.json()

    created = await client.post(
        "/api/v1/wishlist/items",
        headers=headers,
        json={"title": "F1 car", "category": "motorsport"},
    )
    assert created.status_code == 201
    assert created.json()["category"] == "motorsport"

    cats = await client.get("/api/v1/wishlist/categories", headers=headers)
    assert "motorsport" in cats.json()

    filtered = await client.get("/api/v1/wishlist/items?category=motorsport", headers=headers)
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["category"] == "motorsport"


@pytest.mark.asyncio
async def test_wishlist_create_category_endpoint(client):
    token = await _auth_token(client, "wishcats2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/wishlist/categories", headers=headers, json={"name": "gadgets"})
    assert resp.status_code == 201
    assert "gadgets" in resp.json()


@pytest.mark.asyncio
async def test_goal_categories_suggested_and_custom(client):
    token = await _auth_token(client, "goalcats@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    cats = await client.get("/api/v1/goals/categories", headers=headers)
    assert cats.status_code == 200
    assert "career" in cats.json()
    assert "personal" in cats.json()

    created = await client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "Side project", "category": "side-hustle"},
    )
    assert created.status_code == 201
    assert created.json()["category"] == "side-hustle"

    cats = await client.get("/api/v1/goals/categories", headers=headers)
    assert "side-hustle" in cats.json()

    filtered = await client.get("/api/v1/goals?category=side-hustle", headers=headers)
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["category"] == "side-hustle"


@pytest.mark.asyncio
async def test_goal_create_category_endpoint(client):
    token = await _auth_token(client, "goalcats2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/goals/categories", headers=headers, json={"name": "family"})
    assert resp.status_code == 201
    assert "family" in resp.json()


# =========================================================
# Knowledge Notes module
# =========================================================


@pytest.mark.asyncio
async def test_knowledge_notes_full_flow(client):
    token = await _auth_token(client, "kn1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    subject = await client.post(
        "/api/v1/knowledge-notes/subjects",
        headers=headers,
        json={"title": "System Design", "icon": "🧩", "description": "Scalability notes"},
    )
    assert subject.status_code == 201
    subject_id = subject.json()["id"]
    assert subject.json()["chapters"] == []

    chapter = await client.post(
        f"/api/v1/knowledge-notes/subjects/{subject_id}/chapters",
        headers=headers,
        json={"title": "Caching"},
    )
    assert chapter.status_code == 201
    chapter_id = chapter.json()["id"]

    section = await client.post(
        f"/api/v1/knowledge-notes/chapters/{chapter_id}/sections",
        headers=headers,
        json={"title": "Cache invalidation", "content": "# Notes\nThere are only two hard things."},
    )
    assert section.status_code == 201
    section_id = section.json()["id"]

    detail = await client.get(f"/api/v1/knowledge-notes/subjects/{subject_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["chapters"][0]["sections"][0]["title"] == "Cache invalidation"

    listing = await client.get("/api/v1/knowledge-notes/subjects", headers=headers)
    assert listing.json()[0]["chapter_count"] == 1
    assert listing.json()[0]["section_count"] == 1

    search = await client.get("/api/v1/knowledge-notes/search?q=invalidation", headers=headers)
    assert search.status_code == 200
    assert any(h["section_id"] == section_id for h in search.json())

    # Cascade delete.
    deleted = await client.delete(f"/api/v1/knowledge-notes/subjects/{subject_id}", headers=headers)
    assert deleted.status_code == 204
    gone = await client.get(f"/api/v1/knowledge-notes/subjects/{subject_id}", headers=headers)
    assert gone.status_code == 404
    orphan = await client.get(f"/api/v1/knowledge-notes/sections/{section_id}", headers=headers)
    assert orphan.status_code == 404
