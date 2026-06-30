import pytest


async def _auth(client, email="phase2@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Phase2"},
    )
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.mark.asyncio
async def test_learning_crud(client):
    h = await _auth(client)
    created = await client.post(
        "/api/v1/learning/items",
        headers=h,
        json={"title": "Clean Code", "item_type": "book", "status": "in_progress", "progress": 10},
    )
    assert created.status_code == 201
    item_id = created.json()["id"]
    listed = await client.get("/api/v1/learning/items", headers=h)
    assert len(listed.json()) == 1


@pytest.mark.asyncio
async def test_career_and_finance(client):
    h = await _auth(client, "p2b@example.com")
    proj = await client.post(
        "/api/v1/career/projects",
        headers=h,
        json={"name": "LifeOS", "tech_stack": "FastAPI, Angular"},
    )
    assert proj.status_code == 201
    txn = await client.post(
        "/api/v1/finance/transactions",
        headers=h,
        json={"txn_type": "expense", "amount": 50, "category": "food", "txn_date": "2026-06-01"},
    )
    assert txn.status_code == 201
    summary = await client.get("/api/v1/finance/summary", headers=h)
    assert summary.json()["total_expenses"] == 50


@pytest.mark.asyncio
async def test_analytics_timeline_reports_search(client):
    h = await _auth(client, "p2c@example.com")
    await client.post("/api/v1/goals", headers=h, json={"title": "Test goal", "category": "personal"})
    analytics = await client.get("/api/v1/analytics/summary", headers=h)
    assert analytics.status_code == 200
    timeline = await client.get("/api/v1/timeline", headers=h)
    assert timeline.status_code == 200
    assert len(timeline.json()) >= 1
    report = await client.get("/api/v1/reports/weekly", headers=h)
    assert report.status_code == 200
    review = await client.post("/api/v1/reports/reviews/daily", headers=h)
    assert review.status_code == 200
    await client.post("/api/v1/ai/index", headers=h)
    semantic = await client.get("/api/v1/search/semantic", headers=h, params={"q": "goal"})
    assert semantic.status_code == 200
