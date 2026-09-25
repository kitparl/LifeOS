"""News collections: CRUD, memberships, move, pagination, and user isolation."""

from app.tests.conftest import NEWS_RESULT

URL = NEWS_RESULT["url"]


async def _headers(client, email: str) -> dict[str, str]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "usr_" + email.split("@")[0].replace(".", "")[:26],
            "email": email,
            "password": "password123",
            "display_name": "News User",
        },
    )
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


async def _save(client, headers, suffix: str = "") -> dict:
    res = await client.post(
        "/api/v1/news/saved",
        headers=headers,
        json={"article_url": URL + suffix, "title": f"Story {suffix}", "publisher": "The Hindu"},
    )
    return res.json()


async def _collection(client, headers, name: str) -> dict:
    return (await client.post("/api/v1/news/collections", headers=headers, json={"name": name})).json()


def _members_url(collection_id: str) -> str:
    return f"/api/v1/news/collections/{collection_id}/articles"


async def test_create_rename_and_duplicate_names(client):
    headers = await _headers(client, "coll@example.com")
    created = await client.post("/api/v1/news/collections", headers=headers, json={"name": "  AI Research "})
    assert created.status_code == 201
    assert created.json()["name"] == "AI Research"
    assert created.json()["article_count"] == 0

    dup = await client.post("/api/v1/news/collections", headers=headers, json={"name": "ai research"})
    assert dup.status_code == 409
    assert (await client.post("/api/v1/news/collections", headers=headers, json={"name": " "})).status_code == 422
    assert (await client.post("/api/v1/news/collections", headers=headers, json={"name": "x" * 101})).status_code == 422

    cid = created.json()["id"]
    other = await _collection(client, headers, "Business")
    assert (await client.patch(f"/api/v1/news/collections/{cid}", headers=headers, json={"name": "Business"})).status_code == 409
    renamed = await client.patch(f"/api/v1/news/collections/{cid}", headers=headers, json={"name": "AI"})
    assert renamed.status_code == 200 and renamed.json()["name"] == "AI"
    # Renaming to its own name (different case) is allowed.
    same = await client.patch(f"/api/v1/news/collections/{other['id']}", headers=headers, json={"name": "BUSINESS"})
    assert same.status_code == 200

    listing = await client.get("/api/v1/news/collections", headers=headers)
    assert [c["name"] for c in listing.json()] == ["AI", "BUSINESS"]


async def test_add_is_idempotent_many_to_many_and_remove(client):
    headers = await _headers(client, "members@example.com")
    saved = await _save(client, headers)
    ai = await _collection(client, headers, "AI Research")
    later = await _collection(client, headers, "Read Later")

    for _ in range(2):
        res = await client.post(_members_url(ai["id"]), headers=headers, json={"saved_article_id": saved["id"]})
        assert res.status_code == 200
    res = await client.post(_members_url(later["id"]), headers=headers, json={"saved_article_id": saved["id"]})
    assert sorted(res.json()["collection_ids"]) == sorted([ai["id"], later["id"]])

    counts = {c["name"]: c["article_count"] for c in (await client.get("/api/v1/news/collections", headers=headers)).json()}
    assert counts == {"AI Research": 1, "Read Later": 1}

    assert (await client.delete(f"{_members_url(ai['id'])}/{saved['id']}", headers=headers)).status_code == 204
    assert (await client.delete(f"{_members_url(ai['id'])}/{saved['id']}", headers=headers)).status_code == 404
    saved_list = (await client.get("/api/v1/news/saved", headers=headers)).json()
    assert saved_list["items"][0]["collection_ids"] == [later["id"]]


async def test_delete_collection_keeps_saved_articles(client):
    headers = await _headers(client, "delete@example.com")
    saved = await _save(client, headers)
    coll = await _collection(client, headers, "Startup Ideas")
    await client.post(_members_url(coll["id"]), headers=headers, json={"saved_article_id": saved["id"]})

    assert (await client.delete(f"/api/v1/news/collections/{coll['id']}", headers=headers)).status_code == 204
    assert (await client.get("/api/v1/news/collections", headers=headers)).json() == []
    saved_list = (await client.get("/api/v1/news/saved", headers=headers)).json()
    assert saved_list["total"] == 1
    assert saved_list["items"][0]["collection_ids"] == []


async def test_deleting_saved_article_removes_memberships(client):
    headers = await _headers(client, "unsave@example.com")
    saved = await _save(client, headers)
    coll = await _collection(client, headers, "India News")
    await client.post(_members_url(coll["id"]), headers=headers, json={"saved_article_id": saved["id"]})
    await client.delete(f"/api/v1/news/saved/{saved['id']}", headers=headers)
    members = await client.get(_members_url(coll["id"]), headers=headers)
    assert members.json() == {"items": [], "total": 0}


async def test_move_between_collections(client):
    headers = await _headers(client, "move@example.com")
    saved = await _save(client, headers)
    source = await _collection(client, headers, "Inbox")
    target = await _collection(client, headers, "Archive")
    await client.post(_members_url(source["id"]), headers=headers, json={"saved_article_id": saved["id"]})

    same = await client.post(
        f"{_members_url(source['id'])}/{saved['id']}/move", headers=headers, json={"target_collection_id": source["id"]}
    )
    assert same.status_code == 400
    moved = await client.post(
        f"{_members_url(source['id'])}/{saved['id']}/move", headers=headers, json={"target_collection_id": target["id"]}
    )
    assert moved.status_code == 200
    assert moved.json()["collection_ids"] == [target["id"]]
    assert (await client.get(_members_url(source["id"]), headers=headers)).json()["total"] == 0
    assert (await client.get(_members_url(target["id"]), headers=headers)).json()["total"] == 1

    # Not a member of the source any more -> 404.
    again = await client.post(
        f"{_members_url(source['id'])}/{saved['id']}/move", headers=headers, json={"target_collection_id": target["id"]}
    )
    assert again.status_code == 404


async def test_collection_articles_paginated_newest_first(client):
    headers = await _headers(client, "paging@example.com")
    coll = await _collection(client, headers, "AI Research")
    ids = []
    for i in range(3):
        saved = await _save(client, headers, f"?n={i}")
        ids.append(saved["id"])
        await client.post(_members_url(coll["id"]), headers=headers, json={"saved_article_id": saved["id"]})
    page = await client.get(_members_url(coll["id"]), headers=headers, params={"limit": 2, "offset": 0})
    assert page.json()["total"] == 3
    assert [a["id"] for a in page.json()["items"]] == [ids[2], ids[1]]
    rest = await client.get(_members_url(coll["id"]), headers=headers, params={"limit": 2, "offset": 2})
    assert [a["id"] for a in rest.json()["items"]] == [ids[0]]


async def test_user_isolation_on_every_collection_endpoint(client):
    owner = await _headers(client, "own@example.com")
    other = await _headers(client, "intruder@example.com")
    saved = await _save(client, owner)
    coll = await _collection(client, owner, "Private")
    await client.post(_members_url(coll["id"]), headers=owner, json={"saved_article_id": saved["id"]})
    their_saved = await _save(client, other, "?theirs")
    their_coll = await _collection(client, other, "Theirs")

    assert (await client.get("/api/v1/news/collections", headers=other)).json()[0]["name"] == "Theirs"
    checks = [
        client.patch(f"/api/v1/news/collections/{coll['id']}", headers=other, json={"name": "Hacked"}),
        client.delete(f"/api/v1/news/collections/{coll['id']}", headers=other),
        client.get(_members_url(coll["id"]), headers=other),
        client.post(_members_url(coll["id"]), headers=other, json={"saved_article_id": their_saved["id"]}),
        client.delete(f"{_members_url(coll['id'])}/{saved['id']}", headers=other),
        # Their own collection, but the owner's saved article.
        client.post(_members_url(their_coll["id"]), headers=other, json={"saved_article_id": saved["id"]}),
        client.post(
            f"{_members_url(coll['id'])}/{saved['id']}/move",
            headers=other,
            json={"target_collection_id": their_coll["id"]},
        ),
    ]
    for request in checks:
        assert (await request).status_code == 404

    owner_members = await client.get(_members_url(coll["id"]), headers=owner)
    assert owner_members.json()["total"] == 1
