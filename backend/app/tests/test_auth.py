import pytest

@pytest.mark.asyncio
async def test_register_and_login(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "display_name": "Pranshu",
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "test@example.com"

    login = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert login.status_code == 200
