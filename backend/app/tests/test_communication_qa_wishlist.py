import pytest


async def _auth_token(client, email="unit8@example.com"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Unit8 User"},
    )
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_vocabulary_crud(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/communication/vocabulary",
        headers=headers,
        json={"word": "eloquent", "meaning": "fluent and persuasive", "mastery": 2},
    )
    assert create.status_code == 201
    word_id = create.json()["id"]

    listing = await client.get("/api/v1/communication/vocabulary", headers=headers)
    assert listing.status_code == 200
    assert listing.json()[0]["word"] == "eloquent"


@pytest.mark.asyncio
async def test_qa_versioning(client):
    token = await _auth_token(client, "qa@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/qa/entries",
        headers=headers,
        json={"question": "What motivates me?", "answer": "Building useful products", "tags": ["life"]},
    )
    assert create.status_code == 201
    entry_id = create.json()["id"]

    update = await client.patch(
        f"/api/v1/qa/entries/{entry_id}",
        headers=headers,
        json={"answer": "Building useful products and helping others grow"},
    )
    assert update.status_code == 200
    assert len(update.json()["versions"]) == 2

    versions = await client.get(f"/api/v1/qa/entries/{entry_id}/versions", headers=headers)
    assert versions.status_code == 200
    assert len(versions.json()) == 2


@pytest.mark.asyncio
async def test_wishlist_and_dashboard_actions(client):
    token = await _auth_token(client, "wish@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/wishlist/items",
        headers=headers,
        json={"title": "Visit Japan", "category": "travel", "cost": 5000, "progress": 20},
    )
    assert create.status_code == 201

    listing = await client.get("/api/v1/wishlist/items", headers=headers)
    assert listing.status_code == 200
    assert listing.json()[0]["title"] == "Visit Japan"

    summary = await client.get("/api/v1/dashboard/summary", headers=headers)
    actions = {a["id"]: a for a in summary.json()["quick_actions"]}
    assert actions["add_word"]["route"] == "/communication/vocabulary/new"
    assert actions["add_qa"]["route"] == "/qa/new"
    assert actions["add_wishlist"]["route"] == "/wishlist/new"
