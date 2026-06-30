import pytest


async def _auth_token(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "habits@example.com", "password": "password123", "display_name": "Habits User"},
    )
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_create_and_complete_habit(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/habits",
        headers=headers,
        json={"name": "Morning run", "frequency": "daily"},
    )
    assert create.status_code == 201
    habit_id = create.json()["id"]

    complete = await client.post(f"/api/v1/habits/{habit_id}/complete", headers=headers)
    assert complete.status_code == 200
    assert complete.json()["completed_today"] is True
    assert complete.json()["streak"] >= 1


@pytest.mark.asyncio
async def test_list_habits_with_stats(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/habits", headers=headers, json={"name": "Read", "frequency": "daily"})

    listing = await client.get("/api/v1/habits", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert "streak" in listing.json()[0]
    assert "completion_rate" in listing.json()[0]


@pytest.mark.asyncio
async def test_dashboard_habits_today(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/habits",
        headers=headers,
        json={"name": "Meditate", "frequency": "daily"},
    )
    habit_id = create.json()["id"]
    await client.post(f"/api/v1/habits/{habit_id}/complete", headers=headers)

    summary = await client.get("/api/v1/dashboard/summary", headers=headers)
    habits = summary.json()["habits_today"]
    assert len(habits) == 1
    assert habits[0]["name"] == "Meditate"
    assert habits[0]["completed"] is True
