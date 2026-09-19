"""Stage 2 — bookmarks, personal examples, revision, history, progress, search, detail.

Bookmark/unbookmark and Revision/Games must not change sequence (PRD §47 "Bookmark",
"Revision", "Game" tests; §62 rules 11-13).
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from app.modules.communication.vocabulary.models import Vocabulary, VocabularyCollection

pytestmark = pytest.mark.asyncio


async def _auth(client, email: str):
    username = "usr_" + email.split("@")[0].replace(".", "").replace("+", "")[:26]
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "password123", "display_name": "Learner"},
    )
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


async def _seed_vocab(client, count: int = 40) -> None:
    async with client.session_factory() as db:
        collection = VocabularyCollection(name="Test Collection", language="en", version="1.0", status="active")
        db.add(collection)
        await db.flush()
        for i in range(1, count + 1):
            db.add(
                Vocabulary(
                    id=f"v{i:06d}",
                    collection_id=collection.id,
                    sequence_number=i,
                    term=f"word-{i}",
                    type="WORD",
                    level="A2" if i <= 20 else "B1",
                    part_of_speech="noun",
                    simple_meaning=f"meaning {i}",
                    example=f"example sentence {i}",
                    commonness="common",
                    formality="neutral",
                    learning_priority="medium",
                    topics=["work"] if i % 2 == 0 else ["travel"],
                )
            )
        await db.commit()


# --------------------------------------------------------------------------
# Bookmarks
# --------------------------------------------------------------------------

async def test_bookmark_unbookmark_does_not_change_sequence(client):
    await _seed_vocab(client)
    h = await _auth(client, "bm1@example.com")
    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    first_ids = [it["vocabulary"]["id"] for it in today.json()["current_set"]["items"]]

    add = await client.post("/api/v1/communication/vocabulary/bookmarks/v000001", headers=h)
    assert add.status_code == 200, add.text
    assert add.json()["vocabulary"]["id"] == "v000001"

    listed = await client.get("/api/v1/communication/vocabulary/bookmarks", headers=h)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["vocabulary"]["id"] == "v000001"

    removed = await client.delete("/api/v1/communication/vocabulary/bookmarks/v000001", headers=h)
    assert removed.status_code == 204

    listed2 = await client.get("/api/v1/communication/vocabulary/bookmarks", headers=h)
    assert listed2.json()["total"] == 0

    # sequence untouched throughout
    today2 = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    second_ids = [it["vocabulary"]["id"] for it in today2.json()["current_set"]["items"]]
    assert first_ids == second_ids


async def test_bookmark_is_idempotent(client):
    await _seed_vocab(client)
    h = await _auth(client, "bm2@example.com")
    await client.get("/api/v1/communication/vocabulary/today", headers=h)

    first = await client.post("/api/v1/communication/vocabulary/bookmarks/v000001", headers=h)
    second = await client.post("/api/v1/communication/vocabulary/bookmarks/v000001", headers=h)
    assert first.json()["id"] == second.json()["id"]

    listed = await client.get("/api/v1/communication/vocabulary/bookmarks", headers=h)
    assert listed.json()["total"] == 1


async def test_removing_bookmark_preserves_learning_history(client):
    await _seed_vocab(client)
    h = await _auth(client, "bm3@example.com")
    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    set_id = today.json()["current_set"]["id"]
    await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/accept", headers=h)

    await client.post("/api/v1/communication/vocabulary/bookmarks/v000001", headers=h)
    await client.delete("/api/v1/communication/vocabulary/bookmarks/v000001", headers=h)

    detail = await client.get("/api/v1/communication/vocabulary/v000001", headers=h)
    assert detail.status_code == 200
    assert detail.json()["is_bookmarked"] is False
    assert detail.json()["mastery_level"] == 0  # learning history row still exists (not 404)


# --------------------------------------------------------------------------
# Personal examples
# --------------------------------------------------------------------------

async def test_personal_examples_crud_never_touch_master_example(client):
    await _seed_vocab(client)
    h = await _auth(client, "ex1@example.com")
    await client.get("/api/v1/communication/vocabulary/today", headers=h)

    before = await client.get("/api/v1/communication/vocabulary/v000001", headers=h)
    original_example = before.json()["vocabulary"]["example"]

    e1 = await client.post(
        "/api/v1/communication/vocabulary/v000001/examples", headers=h, json={"sentence": "My first example."}
    )
    assert e1.status_code == 200, e1.text
    e2 = await client.post(
        "/api/v1/communication/vocabulary/v000001/examples", headers=h, json={"sentence": "Another one.", "notes": "informal"}
    )
    assert e2.status_code == 200

    listed = await client.get("/api/v1/communication/vocabulary/v000001/examples", headers=h)
    assert len(listed.json()) == 2

    updated = await client.patch(
        f"/api/v1/communication/vocabulary/examples/{e1.json()['id']}", headers=h, json={"sentence": "Edited example."}
    )
    assert updated.status_code == 200
    assert updated.json()["sentence"] == "Edited example."

    deleted = await client.delete(f"/api/v1/communication/vocabulary/examples/{e2.json()['id']}", headers=h)
    assert deleted.status_code == 204

    listed2 = await client.get("/api/v1/communication/vocabulary/v000001/examples", headers=h)
    assert len(listed2.json()) == 1

    after = await client.get("/api/v1/communication/vocabulary/v000001", headers=h)
    assert after.json()["vocabulary"]["example"] == original_example  # master example untouched
    assert after.json()["example_count"] == 1


async def test_cannot_edit_another_users_example(client):
    await _seed_vocab(client)
    ha = await _auth(client, "exA@example.com")
    hb = await _auth(client, "exB@example.com")
    await client.get("/api/v1/communication/vocabulary/today", headers=ha)
    await client.get("/api/v1/communication/vocabulary/today", headers=hb)

    created = await client.post("/api/v1/communication/vocabulary/v000001/examples", headers=ha, json={"sentence": "A's example"})
    example_id = created.json()["id"]

    blocked = await client.patch(
        f"/api/v1/communication/vocabulary/examples/{example_id}", headers=hb, json={"sentence": "hijacked"}
    )
    assert blocked.status_code == 404


# --------------------------------------------------------------------------
# Revision — must never advance next_sequence_number
# --------------------------------------------------------------------------

async def test_revision_all_does_not_advance_sequence(client):
    await _seed_vocab(client)
    h = await _auth(client, "rev1@example.com")

    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    set_id = today.json()["current_set"]["id"]
    await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/accept", headers=h)

    revision = await client.get("/api/v1/communication/vocabulary/revision?source=all", headers=h)
    assert revision.status_code == 200, revision.text
    assert revision.json()["total"] == 10

    # next set must still start at 11 — revision did not consume anything
    next_set = await client.post("/api/v1/communication/vocabulary/sets/next", headers=h)
    ids = [it["vocabulary"]["id"] for it in next_set.json()["items"]]
    assert ids[0] == "v000011"


async def test_revision_by_bookmarked_and_weak_and_level(client):
    await _seed_vocab(client)
    h = await _auth(client, "rev2@example.com")

    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    set_id = today.json()["current_set"]["id"]
    await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/accept", headers=h)
    await client.post("/api/v1/communication/vocabulary/bookmarks/v000003", headers=h)

    bookmarked = await client.get("/api/v1/communication/vocabulary/revision?source=bookmarked", headers=h)
    assert bookmarked.json()["total"] == 1
    assert bookmarked.json()["items"][0]["id"] == "v000003"

    weak = await client.get("/api/v1/communication/vocabulary/revision?source=weak", headers=h)
    assert weak.json()["total"] == 10  # mastery_level starts at 0 <= 2 for all learned items

    level = await client.get("/api/v1/communication/vocabulary/revision?source=level&level=A2", headers=h)
    assert level.json()["total"] == 10  # all 10 seeded items 1-10 are level A2


async def test_revision_requires_date_param_for_specific_day_source(client):
    h = await _auth(client, "rev3@example.com")
    res = await client.get("/api/v1/communication/vocabulary/revision?source=date", headers=h)
    assert res.status_code == 400


# --------------------------------------------------------------------------
# History
# --------------------------------------------------------------------------

async def test_history_reflects_actual_shown_vocabulary_including_changes(client):
    await _seed_vocab(client)
    h = await _auth(client, "hist1@example.com")

    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    set_id = today.json()["current_set"]["id"]
    await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/items/1/change", headers=h)
    await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/accept", headers=h)

    history = await client.get("/api/v1/communication/vocabulary/history", headers=h)
    assert history.status_code == 200
    assert history.json()["total"] == 1
    entry = history.json()["items"][0]
    assert entry["status"] == "accepted"
    assert entry["item_count"] == 10
    assert entry["items"][0]["id"] == "v000011"  # position 1 was changed — history shows what was shown


# --------------------------------------------------------------------------
# Progress dashboard
# --------------------------------------------------------------------------

async def test_progress_dashboard_no_hardcoded_denominator(client):
    await _seed_vocab(client, count=17)
    h = await _auth(client, "prog1@example.com")

    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    set_id = today.json()["current_set"]["id"]
    await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/accept", headers=h)
    await client.post("/api/v1/communication/vocabulary/bookmarks/v000001", headers=h)

    progress = await client.get("/api/v1/communication/vocabulary/progress", headers=h)
    body = progress.json()
    assert body["total_available_vocabulary"] == 17  # matches seeded count, not a literal 15000
    assert body["vocabulary_learned"] == 10
    assert body["bookmarks_count"] == 1
    assert body["needs_revision_count"] == 10
    assert body["current_streak_days"] == 1
    # accepted set is still "today's" set (read-only) until the next IST boundary
    assert body["todays_progress_total"] == 10
    assert body["todays_progress_count"] == 10


async def test_streak_breaks_after_a_missed_day(client):
    await _seed_vocab(client)
    h = await _auth(client, "prog2@example.com")

    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    set_id = today.json()["current_set"]["id"]
    await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/accept", headers=h)

    much_later = date.today() + timedelta(days=5)
    with patch("app.modules.communication.vocabulary.sequencing.ist_today", return_value=much_later), patch(
        "app.modules.communication.vocabulary.service.ist_today", return_value=much_later
    ):
        progress = await client.get("/api/v1/communication/vocabulary/progress", headers=h)
    assert progress.json()["current_streak_days"] == 0


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------

async def test_search_by_term_and_level_and_topic(client):
    await _seed_vocab(client)
    h = await _auth(client, "search1@example.com")

    by_term = await client.get("/api/v1/communication/vocabulary/search?q=word-3", headers=h)
    assert by_term.status_code == 200
    assert any(it["id"] == "v000003" for it in by_term.json()["items"])

    by_level = await client.get("/api/v1/communication/vocabulary/search?level=B1", headers=h)
    assert all(it["level"] == "B1" for it in by_level.json()["items"])
    assert by_level.json()["total"] == 20  # items 21-40 seeded as B1

    by_topic = await client.get("/api/v1/communication/vocabulary/search?topic=travel", headers=h)
    assert by_topic.json()["total"] > 0


async def test_search_is_paginated(client):
    await _seed_vocab(client, count=40)
    h = await _auth(client, "search2@example.com")

    page = await client.get("/api/v1/communication/vocabulary/search?limit=5&offset=0", headers=h)
    assert len(page.json()["items"]) == 5
    assert page.json()["total"] == 40


# --------------------------------------------------------------------------
# Detail
# --------------------------------------------------------------------------

async def test_vocabulary_detail_for_unlearned_item(client):
    await _seed_vocab(client)
    h = await _auth(client, "detail1@example.com")

    detail = await client.get("/api/v1/communication/vocabulary/v000035", headers=h)
    assert detail.status_code == 200
    assert detail.json()["vocabulary"]["id"] == "v000035"
    assert detail.json()["is_bookmarked"] is False
    assert detail.json()["mastery_level"] == 0
    assert detail.json()["example_count"] == 0


async def test_vocabulary_detail_404_for_unknown_id(client):
    h = await _auth(client, "detail2@example.com")
    res = await client.get("/api/v1/communication/vocabulary/v999999", headers=h)
    assert res.status_code == 404
