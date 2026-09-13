"""Pagination contract: limit/offset + X-Total-Count (default page size 25)."""

import pytest


async def _auth(client, username: str, email: str) -> dict[str, str]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
            "display_name": username,
        },
    )
    assert reg.status_code == 201, reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


@pytest.mark.asyncio
async def test_goals_pagination(client):
    headers = await _auth(client, "pagegoals", "pagegoals@example.com")
    for i in range(30):
        r = await client.post(
            "/api/v1/goals",
            headers=headers,
            json={"title": f"Goal {i:02d}", "category": "health"},
        )
        assert r.status_code == 201

    page1 = await client.get("/api/v1/goals", headers=headers, params={"limit": 25, "offset": 0})
    assert page1.status_code == 200
    assert len(page1.json()) == 25
    assert page1.headers.get("X-Total-Count") == "30"

    page2 = await client.get("/api/v1/goals", headers=headers, params={"limit": 25, "offset": 25})
    assert page2.status_code == 200
    assert len(page2.json()) == 5
    assert page2.headers.get("X-Total-Count") == "30"

    defaulted = await client.get("/api/v1/goals", headers=headers)
    assert defaulted.status_code == 200
    assert len(defaulted.json()) == 25


@pytest.mark.asyncio
async def test_journal_pagination(client):
    headers = await _auth(client, "pagejournal", "pagejournal@example.com")
    for i in range(28):
        r = await client.post(
            "/api/v1/journal/entries",
            headers=headers,
            json={
                "entry_date": f"2026-01-{(i % 28) + 1:02d}",
                "entry_type": "morning",
                "title": f"Entry {i}",
                "content": f"Content {i}",
            },
        )
        assert r.status_code == 201, r.text

    page1 = await client.get(
        "/api/v1/journal/entries", headers=headers, params={"limit": 10, "offset": 0}
    )
    assert page1.status_code == 200
    assert len(page1.json()) == 10
    assert page1.headers.get("X-Total-Count") == "28"

    page2 = await client.get(
        "/api/v1/journal/entries", headers=headers, params={"limit": 10, "offset": 20}
    )
    assert page2.status_code == 200
    assert len(page2.json()) == 8
    assert page2.headers.get("X-Total-Count") == "28"


@pytest.mark.asyncio
async def test_habits_pagination(client):
    headers = await _auth(client, "pagehabits", "pagehabits@example.com")
    for i in range(27):
        r = await client.post(
            "/api/v1/habits",
            headers=headers,
            json={"name": f"Habit {i:02d}", "frequency": "daily"},
        )
        assert r.status_code == 201

    listing = await client.get("/api/v1/habits", headers=headers, params={"limit": 25, "offset": 0})
    assert listing.status_code == 200
    assert len(listing.json()) == 25
    assert listing.headers.get("X-Total-Count") == "27"


@pytest.mark.asyncio
async def test_wishlist_pagination(client):
    headers = await _auth(client, "pagewish", "pagewish@example.com")
    for i in range(26):
        r = await client.post(
            "/api/v1/wishlist/items",
            headers=headers,
            json={"title": f"Wish {i:02d}", "category": "gadgets"},
        )
        assert r.status_code == 201

    page1 = await client.get(
        "/api/v1/wishlist/items", headers=headers, params={"limit": 25, "offset": 0}
    )
    assert page1.status_code == 200
    assert len(page1.json()) == 25
    assert page1.headers.get("X-Total-Count") == "26"


@pytest.mark.asyncio
async def test_files_default_limit_is_25(client):
    headers = await _auth(client, "pagefiles", "pagefiles@example.com")
    listing = await client.get("/api/v1/files", headers=headers)
    assert listing.status_code == 200
    assert listing.headers.get("X-Total-Count") == "0"
    assert listing.json() == []


@pytest.mark.asyncio
async def test_notifications_pagination_header(client):
    headers = await _auth(client, "pagenotif", "pagenotif@example.com")
    listing = await client.get(
        "/api/v1/notifications", headers=headers, params={"limit": 25, "offset": 0}
    )
    assert listing.status_code == 200
    assert "X-Total-Count" in listing.headers
