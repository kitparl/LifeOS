import pytest


@pytest.mark.asyncio
async def test_dashboard_summary_requires_auth(client):
    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_summary_empty_state(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dash@example.com",
            "password": "password123",
            "display_name": "Dash User",
        },
    )
    token = reg.json()["access_token"]
    response = await client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sync_status"] == "synced"
    assert data["pending_sync_count"] == 0
    assert data["tasks_today"] == []
    assert data["habits_today"] == []
    assert data["goals_progress"] == []
    assert data["running_progress"] is None
    assert data["calendar_preview"] == []
    assert data["notifications"] == []
    assert data["recent_activity"] == []
    assert len(data["quick_actions"]) >= 1
