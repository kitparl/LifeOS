from datetime import UTC, datetime

import pytest


async def _auth_token(client, email="sticky@example.com"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),
            "email": email,
            "password": "password123",
            "display_name": "Sticky User",
        },
    )
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_create_note_defaults_and_month_grouping(client):
    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "Buy milk"})
    assert create.status_code == 201
    note = create.json()
    assert note["color"] == "yellow"
    assert note["is_pinned"] is False
    current_month = datetime.now(UTC).strftime("%Y-%m")
    assert note["note_month"] == current_month

    months = await client.get("/api/v1/sticky-notes/months", headers=headers)
    assert months.status_code == 200
    assert {"month": current_month, "note_count": 1} in months.json()

    listing = await client.get("/api/v1/sticky-notes", headers=headers, params={"month": current_month})
    assert listing.status_code == 200
    assert listing.json()[0]["content"] == "Buy milk"


@pytest.mark.asyncio
async def test_newest_note_sorts_first_by_default(client):
    token = await _auth_token(client, "order@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    current_month = datetime.now(UTC).strftime("%Y-%m")

    first = await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "First"})
    second = await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "Second"})
    assert first.status_code == 201 and second.status_code == 201

    listing = await client.get("/api/v1/sticky-notes", headers=headers, params={"month": current_month})
    contents = [n["content"] for n in listing.json()]
    assert contents == ["Second", "First"]


@pytest.mark.asyncio
async def test_pinned_notes_sort_before_unpinned(client):
    token = await _auth_token(client, "pin@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    current_month = datetime.now(UTC).strftime("%Y-%m")

    await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "Newer"})
    older = await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "Older"})
    note_id = older.json()["id"]

    pin = await client.patch(f"/api/v1/sticky-notes/{note_id}", headers=headers, json={"is_pinned": True})
    assert pin.status_code == 200

    listing = await client.get("/api/v1/sticky-notes", headers=headers, params={"month": current_month})
    contents = [n["content"] for n in listing.json()]
    assert contents[0] == "Older"


@pytest.mark.asyncio
async def test_reorder_via_patch_order_index(client):
    token = await _auth_token(client, "reorder@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    current_month = datetime.now(UTC).strftime("%Y-%m")

    a = (await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "A"})).json()
    b = (await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "B"})).json()

    # B currently sorts first (newest-first default); move A above B.
    await client.patch(f"/api/v1/sticky-notes/{a['id']}", headers=headers, json={"order_index": b["order_index"] - 1})

    listing = await client.get("/api/v1/sticky-notes", headers=headers, params={"month": current_month})
    contents = [n["content"] for n in listing.json()]
    assert contents == ["A", "B"]


@pytest.mark.asyncio
async def test_list_all_returns_notes_across_months(client):
    token = await _auth_token(client, "all@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "A"})
    await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "B"})

    listing = await client.get("/api/v1/sticky-notes/all", headers=headers)
    assert listing.status_code == 200
    assert {n["content"] for n in listing.json()} == {"A", "B"}


@pytest.mark.asyncio
async def test_search_across_months(client):
    token = await _auth_token(client, "search@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/sticky-notes", headers=headers, json={"title": "Groceries", "content": "eggs"})
    await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "unrelated"})

    results = await client.get("/api/v1/sticky-notes/search", headers=headers, params={"q": "grocer"})
    assert results.status_code == 200
    assert len(results.json()) == 1
    assert results.json()[0]["title"] == "Groceries"


@pytest.mark.asyncio
async def test_delete_note_is_soft_delete(client):
    token = await _auth_token(client, "delete@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    current_month = datetime.now(UTC).strftime("%Y-%m")

    created = (await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "temp"})).json()

    delete = await client.delete(f"/api/v1/sticky-notes/{created['id']}", headers=headers)
    assert delete.status_code == 204

    get_after = await client.get(f"/api/v1/sticky-notes/{created['id']}", headers=headers)
    assert get_after.status_code == 404

    listing = await client.get("/api/v1/sticky-notes", headers=headers, params={"month": current_month})
    assert listing.json() == []

    from app.modules.sticky_notes.models import StickyNote
    from sqlalchemy import select

    async with client.session_factory() as db:
        rec = (await db.execute(select(StickyNote).where(StickyNote.id == created["id"]))).scalar_one()
        assert rec.deleted_at is not None


@pytest.mark.asyncio
async def test_restore_note(client):
    token = await _auth_token(client, "restore@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = (await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "bring back"})).json()
    await client.delete(f"/api/v1/sticky-notes/{created['id']}", headers=headers)

    restored = await client.post(f"/api/v1/sticky-notes/{created['id']}/restore", headers=headers)
    assert restored.status_code == 200
    assert restored.json()["deleted_at"] is None

    get_after = await client.get(f"/api/v1/sticky-notes/{created['id']}", headers=headers)
    assert get_after.status_code == 200


@pytest.mark.asyncio
async def test_list_deleted_and_restore_from_it(client):
    token = await _auth_token(client, "listdeleted@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    kept = (await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "kept"})).json()
    trashed = (await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "trashed"})).json()
    await client.delete(f"/api/v1/sticky-notes/{trashed['id']}", headers=headers)

    deleted_list = await client.get("/api/v1/sticky-notes/deleted", headers=headers)
    assert deleted_list.status_code == 200
    assert [n["id"] for n in deleted_list.json()] == [trashed["id"]]
    assert kept["id"] not in [n["id"] for n in deleted_list.json()]

    restore = await client.post(f"/api/v1/sticky-notes/{trashed['id']}/restore", headers=headers)
    assert restore.status_code == 200

    deleted_after = await client.get("/api/v1/sticky-notes/deleted", headers=headers)
    assert deleted_after.json() == []


@pytest.mark.asyncio
async def test_purge_hard_deletes_after_retention(client):
    from datetime import timedelta

    from app.modules.sticky_notes.models import StickyNote
    from app.modules.sticky_notes.service import STICKY_NOTES_PURGE_AFTER_DAYS, StickyNoteService
    from sqlalchemy import select

    token = await _auth_token(client, "purge@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = (await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "old"})).json()
    await client.delete(f"/api/v1/sticky-notes/{created['id']}", headers=headers)

    async with client.session_factory() as db:
        rec = (await db.execute(select(StickyNote).where(StickyNote.id == created["id"]))).scalar_one()
        rec.deleted_at = datetime.now(UTC) - timedelta(days=STICKY_NOTES_PURGE_AFTER_DAYS + 1)
        await db.commit()

    async with client.session_factory() as db:
        purged = await StickyNoteService(db).purge_expired()
        await db.commit()
    assert purged == 1

    async with client.session_factory() as db:
        rec = (await db.execute(select(StickyNote).where(StickyNote.id == created["id"]))).scalar_one_or_none()
        assert rec is None


@pytest.mark.asyncio
async def test_notes_are_scoped_per_user(client):
    token_a = await _auth_token(client, "owner-a@example.com")
    token_b = await _auth_token(client, "owner-b@example.com")

    created = await client.post(
        "/api/v1/sticky-notes", headers={"Authorization": f"Bearer {token_a}"}, json={"content": "mine"}
    )
    note_id = created.json()["id"]

    cross_access = await client.get(
        f"/api/v1/sticky-notes/{note_id}", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert cross_access.status_code == 404


@pytest.mark.asyncio
async def test_tags_are_normalized_on_create(client):
    token = await _auth_token(client, "tagnorm@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/sticky-notes",
        headers=headers,
        json={"content": "standup notes", "tags": ["#Scrum", "  meeting ", "#scrum", "New Requirement!", ""]},
    )
    assert created.status_code == 201
    # "#Scrum" and "#scrum" collapse to one; case-folded, '#' stripped, invalid
    # chars dropped, blank entries dropped, order of first occurrence kept.
    assert created.json()["tags"] == ["scrum", "meeting", "newrequirement"]


@pytest.mark.asyncio
async def test_tags_persist_across_update_and_reload(client):
    token = await _auth_token(client, "tagpersist@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = (
        await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "sprint planning"})
    ).json()
    assert created["tags"] == []

    updated = await client.patch(
        f"/api/v1/sticky-notes/{created['id']}", headers=headers, json={"tags": ["scrum", "meeting"]}
    )
    assert updated.status_code == 200
    assert updated.json()["tags"] == ["scrum", "meeting"]

    reloaded = await client.get(f"/api/v1/sticky-notes/{created['id']}", headers=headers)
    assert reloaded.json()["tags"] == ["scrum", "meeting"]

    # Removing a chip: PATCH with the remaining tags only.
    removed = await client.patch(
        f"/api/v1/sticky-notes/{created['id']}", headers=headers, json={"tags": ["scrum"]}
    )
    assert removed.json()["tags"] == ["scrum"]


@pytest.mark.asyncio
async def test_search_matches_tag_with_or_without_hash(client):
    token = await _auth_token(client, "tagsearch@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    tagged = (
        await client.post(
            "/api/v1/sticky-notes",
            headers=headers,
            json={"title": "Standup", "content": "unrelated body text", "tags": ["meeting"]},
        )
    ).json()
    await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "no tags here"})

    by_hash = await client.get("/api/v1/sticky-notes/search", headers=headers, params={"q": "#meeting"})
    assert [n["id"] for n in by_hash.json()] == [tagged["id"]]

    by_plain = await client.get("/api/v1/sticky-notes/search", headers=headers, params={"q": "meeting"})
    assert [n["id"] for n in by_plain.json()] == [tagged["id"]]


@pytest.mark.asyncio
async def test_search_multi_tag_requires_all_tags(client):
    token = await _auth_token(client, "multitag@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    both = (
        await client.post(
            "/api/v1/sticky-notes", headers=headers, json={"content": "a", "tags": ["scrum", "meeting"]}
        )
    ).json()
    only_scrum = (
        await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "b", "tags": ["scrum"]})
    ).json()

    results = await client.get(
        "/api/v1/sticky-notes/search", headers=headers, params={"q": "#scrum #meeting"}
    )
    ids = [n["id"] for n in results.json()]
    assert ids == [both["id"]]
    assert only_scrum["id"] not in ids


@pytest.mark.asyncio
async def test_title_content_search_unaffected_by_tags(client):
    token = await _auth_token(client, "textsearch@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/sticky-notes", headers=headers, json={"title": "Groceries", "content": "eggs"})
    await client.post("/api/v1/sticky-notes", headers=headers, json={"content": "unrelated"})

    results = await client.get("/api/v1/sticky-notes/search", headers=headers, params={"q": "grocer"})
    assert results.status_code == 200
    assert len(results.json()) == 1
    assert results.json()[0]["title"] == "Groceries"


@pytest.mark.parametrize(
    ("stored", "expected"),
    [(None, []), ([], []), ("[]", []), ('["work", "home"]', ["work", "home"]), ("not json", [])],
)
def test_response_accepts_tags_stored_as_json_text(stored, expected):
    # Postgres returns the TEXT-backed JSON column as a raw string.
    from app.modules.sticky_notes.schemas import StickyNoteResponse

    now = datetime.now(UTC)
    resp = StickyNoteResponse.model_validate(
        {
            "id": "n1", "title": None, "content": "x", "color": "yellow", "is_pinned": False,
            "order_index": 0, "note_month": "2026-09", "tags": stored, "created_at": now, "updated_at": now,
        }
    )
    assert resp.tags == expected
