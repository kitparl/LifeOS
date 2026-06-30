from datetime import UTC, datetime, timedelta

import pytest


async def _auth_token(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "tasks@example.com", "password": "password123", "display_name": "Tasks User"},
    )
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_create_and_list_tasks(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Write docs", "priority": "high", "tags": ["work"]},
    )
    assert create.status_code == 201
    assert create.json()["title"] == "Write docs"
    assert create.json()["tags"] == ["work"]

    listing = await client.get("/api/v1/tasks", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


@pytest.mark.asyncio
async def test_complete_task(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Ship feature"},
    )
    task_id = create.json()["id"]

    done = await client.post(f"/api/v1/tasks/{task_id}/complete", headers=headers)
    assert done.status_code == 200
    assert done.json()["status"] == "completed"
    assert done.json()["completed_at"] is not None


@pytest.mark.asyncio
async def test_subtask(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    parent = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Parent task"},
    )
    parent_id = parent.json()["id"]

    sub = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Subtask one", "parent_id": parent_id},
    )
    assert sub.status_code == 201

    detail = await client.get(f"/api/v1/tasks/{parent_id}", headers=headers)
    assert len(detail.json()["subtasks"]) == 1


@pytest.mark.asyncio
async def test_dashboard_tasks_today(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    due = datetime.now(UTC).replace(hour=14, minute=0, second=0, microsecond=0)
    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Due today", "due_date": due.isoformat()},
    )
    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Future task", "due_date": (due + timedelta(days=3)).isoformat()},
    )

    summary = await client.get("/api/v1/dashboard/summary", headers=headers)
    tasks = summary.json()["tasks_today"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Due today"
