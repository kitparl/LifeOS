import pytest


async def _auth(client, email="phase2@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={
        "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),"email": email, "password": "password123", "display_name": "Phase2"},
    )
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.mark.asyncio
async def test_finance_transactions(client):
    h = await _auth(client, "p2b@example.com")
    txn = await client.post(
        "/api/v1/finance/transactions",
        headers=h,
        json={"txn_type": "expense", "amount": 50, "category": "food", "txn_date": "2026-06-01"},
    )
    assert txn.status_code == 201
    summary = await client.get("/api/v1/finance/summary", headers=h)
    assert summary.json()["total_expenses"] == 50


@pytest.mark.asyncio
async def test_semantic_search(client):
    h = await _auth(client, "p2c@example.com")
    await client.post("/api/v1/tasks", headers=h, json={"title": "Test task"})
    await client.post("/api/v1/ai/index", headers=h)
    semantic = await client.get("/api/v1/search/semantic", headers=h, params={"q": "task"})
    assert semantic.status_code == 200
