import pytest


async def _auth_token(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "goals@example.com", "password": "password123", "display_name": "Goals User"},
    )
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_create_and_list_goals(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "Run a marathon", "category": "running", "progress": 10},
    )
    assert create.status_code == 201
    goal = create.json()
    assert goal["title"] == "Run a marathon"
    assert goal["category"] == "running"
    assert goal["status"] == "active"

    listing = await client.get("/api/v1/goals", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


@pytest.mark.asyncio
async def test_goal_milestones_update_progress(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "Learn Angular", "category": "learning"},
    )
    goal_id = create.json()["id"]

    ms = await client.post(
        f"/api/v1/goals/{goal_id}/milestones",
        headers=headers,
        json={"title": "Complete Unit 3"},
    )
    assert ms.status_code == 201
    milestone_id = ms.json()["id"]

    complete = await client.patch(
        f"/api/v1/goals/{goal_id}/milestones/{milestone_id}",
        headers=headers,
        json={"completed": True},
    )
    assert complete.status_code == 200

    goal = await client.get(f"/api/v1/goals/{goal_id}", headers=headers)
    assert goal.json()["progress"] == 100


@pytest.mark.asyncio
async def test_archive_goal(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "Old goal", "category": "personal"},
    )
    goal_id = create.json()["id"]

    archived = await client.post(f"/api/v1/goals/{goal_id}/archive", headers=headers)
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"


@pytest.mark.asyncio
async def test_dashboard_includes_goals_progress(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/goals",
        headers=headers,
        json={"title": "Career goal", "category": "career", "progress": 25},
    )

    summary = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    goals = summary.json()["goals_progress"]
    assert len(goals) == 1
    assert goals[0]["title"] == "Career goal"
    assert goals[0]["percent"] == 25
