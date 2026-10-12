import pytest


async def _auth_token(client, email="unit8@example.com"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
        "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),"email": email, "password": "password123", "display_name": "Unit8 User"},
    )
    return reg.json()["access_token"]


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
async def test_wishlist_create_and_list(client):
    token = await _auth_token(client, "wish@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/wishlist/items",
        headers=headers,
        json={"title": "Visit Japan", "category": "travel", "target_year": 2027, "status": "in_progress", "priority": "high"},
    )
    assert create.status_code == 201

    listing = await client.get("/api/v1/wishlist/items", headers=headers)
    assert listing.status_code == 200
    assert listing.json()[0]["title"] == "Visit Japan"



FILE_ID = "65971633-421b-400c-a144-965a82ffc04e"
CANONICAL = f"/api/v1/files/{FILE_ID}/content"


@pytest.mark.asyncio
async def test_wishlist_photos_are_stored_as_canonical_file_urls(client):
    headers = {"Authorization": f"Bearer {await _auth_token(client, 'wishphoto@example.com')}"}
    external = "https://example.com/" + "long/" * 120 + "pic.jpg"  # > 500 chars: fine as a photo, not a cover field

    create = await client.post(
        "/api/v1/wishlist/items",
        headers=headers,
        json={
            "title": "Northern lights",
            "photos": [f"http://localhost:8000{CANONICAL}", f"{CANONICAL}?token=abc", external],
        },
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["photos"] == [CANONICAL, CANONICAL, external]
    assert body["image_url"] == CANONICAL

    fetched = (await client.get(f"/api/v1/wishlist/items/{body['id']}", headers=headers)).json()
    assert fetched["photos"] == body["photos"]

    update = await client.patch(
        f"/api/v1/wishlist/items/{body['id']}",
        headers=headers,
        json={"title": "Aurora", "photos": [external, f"{CANONICAL}?token=xyz"]},
    )
    assert update.status_code == 200, update.text
    assert update.json()["photos"] == [external, CANONICAL]
    assert update.json()["image_url"] == external

    cleared = await client.patch(f"/api/v1/wishlist/items/{body['id']}", headers=headers, json={"photos": []})
    assert cleared.json()["photos"] == [] and cleared.json()["image_url"] is None

    listing = (await client.get("/api/v1/wishlist/items", headers=headers)).json()
    assert listing[0]["image_url"] is None


def test_wishlist_response_reads_photos_stored_as_json_text():
    from datetime import datetime

    from app.modules.wishlist.schemas import WishlistResponse

    now = datetime(2026, 1, 1)
    row = {
        "id": "i", "title": "t", "description": None, "category": "other", "target_year": None,
        "achieved_date": None, "status": "in_progress", "priority": "medium", "notes": None,
        "image_url": None, "created_at": now, "updated_at": now,
    }  # fmt: skip
    from_text = WishlistResponse.model_validate({**row, "photos": f'["http://localhost:8000{CANONICAL}"]'})
    assert from_text.photos == [CANONICAL] and from_text.image_url == CANONICAL
    assert WishlistResponse.model_validate({**row, "photos": "not json"}).photos == []
    assert WishlistResponse.model_validate({**row, "photos": None}).photos == []
