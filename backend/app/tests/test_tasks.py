from datetime import datetime, timedelta, timezone

import pytest


async def _auth_token(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
        "username": "taskuser","email": "tasks@example.com", "password": "password123", "display_name": "Tasks User"},
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

    due = datetime.now(timezone.utc).replace(hour=14, minute=0, second=0, microsecond=0)
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


@pytest.mark.asyncio
async def test_list_tasks_due_date_filters(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(timezone.utc)
    today = now.replace(hour=12, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "No due", "priority": "low"},
    )
    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Due today", "due_date": today.isoformat()},
    )
    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Overdue open", "due_date": yesterday.isoformat()},
    )
    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Future", "due_date": tomorrow.isoformat()},
    )

    overdue_done = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Overdue done", "due_date": yesterday.isoformat()},
    )
    await client.post(
        f"/api/v1/tasks/{overdue_done.json()['id']}/complete",
        headers=headers,
    )

    without = await client.get(
        "/api/v1/tasks",
        headers=headers,
        params={"has_due_date": "false"},
    )
    assert without.status_code == 200
    assert {t["title"] for t in without.json()} == {"No due"}

    with_due = await client.get(
        "/api/v1/tasks",
        headers=headers,
        params={"has_due_date": "true"},
    )
    assert with_due.status_code == 200
    assert {t["title"] for t in with_due.json()} == {
        "Due today",
        "Overdue open",
        "Future",
        "Overdue done",
    }

    today_list = await client.get(
        "/api/v1/tasks",
        headers=headers,
        params={"due_today": "true", "incomplete_only": "true"},
    )
    assert today_list.status_code == 200
    assert [t["title"] for t in today_list.json()] == ["Due today"]

    overdue_list = await client.get(
        "/api/v1/tasks",
        headers=headers,
        params={"overdue": "true"},
    )
    assert overdue_list.status_code == 200
    assert {t["title"] for t in overdue_list.json()} == {"Overdue open"}


@pytest.mark.asyncio
async def test_list_tasks_due_later(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(timezone.utc)
    today = now.replace(hour=12, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Today task", "due_date": today.isoformat()},
    )
    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Future task", "due_date": tomorrow.isoformat()},
    )

    later = await client.get(
        "/api/v1/tasks",
        headers=headers,
        params={"due_later": "true"},
    )
    assert later.status_code == 200
    assert [t["title"] for t in later.json()] == ["Future task"]


@pytest.mark.asyncio
async def test_list_tasks_exclude_due_today_inbox(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(timezone.utc)
    today = now.replace(hour=12, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Today task", "due_date": today.isoformat()},
    )
    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Inbox no date"},
    )
    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Future task", "due_date": tomorrow.isoformat()},
    )

    inbox = await client.get(
        "/api/v1/tasks",
        headers=headers,
        params={"exclude_due_today": "true", "incomplete_only": "true"},
    )
    assert inbox.status_code == 200
    assert {t["title"] for t in inbox.json()} == {"Inbox no date", "Future task"}


@pytest.mark.asyncio
async def test_list_tasks_pagination_and_total_count(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(15):
        await client.post(
            "/api/v1/tasks",
            headers=headers,
            json={"title": f"Task {i:02d}"},
        )

    page1 = await client.get(
        "/api/v1/tasks",
        headers=headers,
        params={"has_due_date": "false", "limit": 10, "offset": 0},
    )
    assert page1.status_code == 200
    assert len(page1.json()) == 10
    assert page1.headers.get("X-Total-Count") == "15"

    page2 = await client.get(
        "/api/v1/tasks",
        headers=headers,
        params={"has_due_date": "false", "limit": 10, "offset": 10},
    )
    assert page2.status_code == 200
    assert len(page2.json()) == 5
    assert page2.headers.get("X-Total-Count") == "15"


@pytest.mark.asyncio
async def test_task_stats(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Done task"},
    )
    task_id = create.json()["id"]
    await client.post(f"/api/v1/tasks/{task_id}/complete", headers=headers)

    stats = await client.get("/api/v1/tasks/stats", headers=headers)
    assert stats.status_code == 200
    body = stats.json()
    assert body["completed_today"] == 1
    assert body["streak_days"] >= 1
