import pytest


async def _auth_token(client, email="unit9@example.com"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Unit9 User"},
    )
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_global_search(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "Marathon training uniquexyz", "category": "running"},
    )

    result = await client.get("/api/v1/search", headers=headers, params={"q": "uniquexyz"})
    assert result.status_code == 200
    data = result.json()
    assert data["total"] >= 1
    assert data["results"][0]["module"] == "goals"


@pytest.mark.asyncio
async def test_notifications_crud(client):
    token = await _auth_token(client, "notify@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/notifications",
        headers=headers,
        json={"message": "Task due today", "route": "/tasks"},
    )
    assert create.status_code == 201
    nid = create.json()["id"]

    listing = await client.get("/api/v1/notifications", headers=headers, params={"unread_only": True})
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    read = await client.patch(f"/api/v1/notifications/{nid}/read", headers=headers)
    assert read.status_code == 200
    assert read.json()["is_read"] is True


@pytest.mark.asyncio
async def test_export_goals_json(client):
    token = await _auth_token(client, "export@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "Export goal", "category": "personal"},
    )

    resp = await client.get("/api/v1/export/goals", headers=headers, params={"format": "json"})
    assert resp.status_code == 200
    assert "Export goal" in resp.text


@pytest.mark.asyncio
async def test_dashboard_notifications(client):
    token = await _auth_token(client, "dash9@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/notifications",
        headers=headers,
        json={"message": "Welcome to LifeOS"},
    )

    summary = await client.get("/api/v1/dashboard/summary", headers=headers)
    notifications = summary.json()["notifications"]
    assert len(notifications) == 1
    actions = {a["id"]: a for a in summary.json()["quick_actions"]}
    assert actions["export_data"]["route"] == "/export"
