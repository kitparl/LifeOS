"""Tests for Analytics Dashboard module."""

import pytest
from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, email: str = "analytics_dash@example.com") -> dict[str, str]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Analytics User"},
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_analytics_dashboard_requires_auth(client: AsyncClient):
    res = await client.get("/api/v1/analytics/dashboard")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_analytics_dashboard_empty_overview(client: AsyncClient):
    headers = await _auth_headers(client, "overview@example.com")
    res = await client.get("/api/v1/analytics/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "life_score" in data
    assert "kpis" in data
    assert len(data["kpis"]) == 10
    assert data["todays_tasks"] == 0
    assert data["focus_time_label"] == "planned"


@pytest.mark.asyncio
async def test_analytics_dashboard_all_endpoints(client: AsyncClient):
    headers = await _auth_headers(client, "allends@example.com")
    paths = [
        "/api/v1/analytics/dashboard",
        "/api/v1/analytics/dashboard/summary",
        "/api/v1/analytics/dashboard/productivity",
        "/api/v1/analytics/dashboard/goals",
        "/api/v1/analytics/dashboard/habits",
        "/api/v1/analytics/dashboard/journal",
        "/api/v1/analytics/dashboard/ai",
        "/api/v1/analytics/dashboard/widgets",
    ]
    for path in paths:
        res = await client.get(path, headers=headers)
        assert res.status_code == 200, f"{path} -> {res.status_code} {res.text}"


@pytest.mark.asyncio
async def test_analytics_dashboard_ai_coming_soon(client: AsyncClient):
    headers = await _auth_headers(client, "ai@example.com")
    res = await client.get("/api/v1/analytics/dashboard/ai", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["daily"]["status"] == "coming_soon"
    assert data["weekly"]["status"] == "coming_soon"
    assert data["monthly"]["status"] == "coming_soon"
    assert data["predictions"]["status"] == "coming_soon"


@pytest.mark.asyncio
async def test_analytics_dashboard_with_seeded_task(client: AsyncClient):
    headers = await _auth_headers(client, "seed@example.com")
    create = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Analytics seed task"},
    )
    assert create.status_code == 201
    task_id = create.json()["id"]
    done = await client.post(f"/api/v1/tasks/{task_id}/complete", headers=headers)
    assert done.status_code == 200

    res = await client.get("/api/v1/analytics/dashboard/productivity", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "daily_tasks" in data
    assert "calendar_heatmap" in data
    assert isinstance(data["overdue_tasks"], int)


@pytest.mark.asyncio
async def test_existing_analytics_untouched(client: AsyncClient):
    headers = await _auth_headers(client, "legacy@example.com")
    res = await client.get("/api/v1/analytics/summary", headers=headers)
    assert res.status_code == 200
    assert "tasks_completed" in res.json()
