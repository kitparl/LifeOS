import pytest


async def _auth_token(client, email="prefs@example.com"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
        "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),"email": email, "password": "password123", "display_name": "Prefs User"},
    )
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_preferences_get_put_list(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    empty = await client.get("/api/v1/preferences/nav", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["key"] == "nav"
    assert empty.json()["value"] is None

    payload = {
        "value": {
            "categoryOrder": ["Core", "Health"],
            "moduleCategory": {"dashboard": "Core"},
            "order": {"Core": ["dashboard"]},
            "pinnedTop": ["dashboard"],
            "visible": ["dashboard", "tasks"],
        }
    }
    put = await client.put("/api/v1/preferences/nav", headers=headers, json=payload)
    assert put.status_code == 200, put.text
    assert put.json()["value"]["pinnedTop"] == ["dashboard"]
    assert put.json()["value"]["visible"] == ["dashboard", "tasks"]

    got = await client.get("/api/v1/preferences/nav", headers=headers)
    assert got.status_code == 200
    assert got.json()["value"]["visible"] == ["dashboard", "tasks"]

    listing = await client.get("/api/v1/preferences", headers=headers)
    assert listing.status_code == 200
    assert any(item["key"] == "nav" for item in listing.json())
