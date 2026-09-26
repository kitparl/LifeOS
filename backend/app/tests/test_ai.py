import pytest


async def _auth_token(client, email="ai@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={
        "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),"email": email, "password": "password123", "display_name": "AI User"},
    )
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_ai_status_without_provider(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get("/api/v1/ai/status", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["enabled"] is False
    assert body["provider"] == "none"


@pytest.mark.asyncio
async def test_ai_index_and_chat_without_provider(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    task = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Marathon 2026", "description": "Train for Berlin"},
    )
    assert task.status_code == 201

    index = await client.post("/api/v1/ai/index", headers=headers)
    assert index.status_code == 200
    assert index.json()["indexed"] >= 1

    chat = await client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "How is my Marathon training going?"},
    )
    assert chat.status_code == 200
    body = chat.json()
    assert "reply" in body
    assert "Marathon" in body["reply"] or any("Marathon" in s["title"] for s in body["sources"])
