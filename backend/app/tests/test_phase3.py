import pytest


async def _auth(client, email="phase3@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={
        "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),"email": email, "password": "password123", "display_name": "Phase3"},
    )
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.mark.asyncio
async def test_memory_crud(client):
    h = await _auth(client)
    created = await client.post(
        "/api/v1/memory/items",
        headers=h,
        json={"memory_key": "wake_time", "memory_value": "6:00 AM", "category": "preference"},
    )
    assert created.status_code == 201
    summary = await client.get("/api/v1/memory/summary", headers=h)
    assert summary.json()["total"] == 1


@pytest.mark.asyncio
async def test_ocr_integrations(client):
    h = await _auth(client, "p3ovi@example.com")
    ocr = await client.post(
        "/api/v1/ocr/documents",
        headers=h,
        json={"filename": "receipt.txt", "doc_type": "receipt", "text": "Total: $12.50"},
    )
    assert ocr.status_code == 201
    providers = await client.get("/api/v1/integrations/providers", headers=h)
    assert len(providers.json()) >= 5
    conn = await client.post("/api/v1/integrations", headers=h, json={"provider": "telegram", "enabled": True})
    assert conn.status_code == 201
