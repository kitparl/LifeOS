"""Core sequencing/daily-state-machine rules — PRD §47 test list, §62 non-negotiable rules.

Master vocabulary fixture rows are inserted directly against the test DB (via the
`client.session_factory` exposed in conftest.py) rather than through the HTTP API —
importing is a standalone CLI script (app.modules.communication.vocabulary.seeder), not an endpoint.
"""

import asyncio
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from app.modules.communication.vocabulary.models import Vocabulary, VocabularyCollection

pytestmark = pytest.mark.asyncio


async def _auth(client, email: str):
    username = "usr_" + email.split("@")[0].replace(".", "").replace("+", "")[:26]
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
            "display_name": "Learner",
        },
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
                    level="A2",
                    part_of_speech="noun",
                    simple_meaning=f"meaning {i}",
                    example=f"example sentence {i}",
                    commonness="common",
                    formality="neutral",
                    learning_priority="medium",
                )
            )
        await db.commit()


def _ids(items: list[dict]) -> list[str]:
    return [it["vocabulary"]["id"] for it in items]


# --------------------------------------------------------------------------
# PRD §47 "Sequence tests" — new user gets 1-10, accept advances to 11, next day 11-20
# --------------------------------------------------------------------------

async def test_new_user_gets_first_ten_in_order(client):
    await _seed_vocab(client)
    h = await _auth(client, "seq1@example.com")

    res = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["state"] == "ACTIVE"
    assert body["current_set"]["status"] == "active"
    assert body["current_set"]["set_type"] == "daily"
    ids = _ids(body["current_set"]["items"])
    assert ids == [f"v{i:06d}" for i in range(1, 11)]
    positions = [it["position"] for it in body["current_set"]["items"]]
    assert positions == list(range(1, 11))


async def test_accept_then_next_day_gives_next_ten(client):
    await _seed_vocab(client)
    h = await _auth(client, "seq2@example.com")

    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    set_id = today.json()["current_set"]["id"]

    accepted = await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/accept", headers=h)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "accepted"

    tomorrow = date.today() + timedelta(days=1)
    with patch("app.modules.communication.vocabulary.sequencing.ist_today", return_value=tomorrow):
        res = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    body = res.json()
    assert body["state"] == "ACTIVE_NEXT_SET"
    assert _ids(body["current_set"]["items"]) == [f"v{i:06d}" for i in range(11, 21)]


# --------------------------------------------------------------------------
# PRD §47 "Unaccepted test" — midnight passing must NOT advance an unaccepted set
# --------------------------------------------------------------------------

async def test_unaccepted_set_persists_across_midnight(client):
    await _seed_vocab(client)
    h = await _auth(client, "seq3@example.com")

    first = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    first_ids = _ids(first.json()["current_set"]["items"])

    later = date.today() + timedelta(days=3)
    with patch("app.modules.communication.vocabulary.sequencing.ist_today", return_value=later):
        res = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    body = res.json()
    assert body["state"] == "ACTIVE"
    assert body["current_set"]["status"] == "active"
    assert _ids(body["current_set"]["items"]) == first_ids


# --------------------------------------------------------------------------
# PRD §47 "Change test" — change advances next_sequence, never reuses replaced ids
# --------------------------------------------------------------------------

async def test_change_word_allocates_next_unused_and_never_repeats(client):
    await _seed_vocab(client)
    h = await _auth(client, "seq4@example.com")

    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    set_id = today.json()["current_set"]["id"]
    original_ids = _ids(today.json()["current_set"]["items"])
    assert original_ids[4] == "v000005"

    changed = await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/items/5/change", headers=h)
    assert changed.status_code == 200, changed.text
    new_ids = _ids(changed.json()["items"])
    assert new_ids[4] == "v000011"
    assert new_ids.count("v000005") == 0  # replaced id never reappears in the set
    assert changed.json()["items"][4]["was_changed"] is True

    changed_again = await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/items/5/change", headers=h)
    assert _ids(changed_again.json()["items"])[4] == "v000012"

    # next daily set (after accept) must continue from 13, not repeat 5 or 11
    accept_res = await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/accept", headers=h)
    assert accept_res.status_code == 200
    tomorrow = date.today() + timedelta(days=1)
    with patch("app.modules.communication.vocabulary.sequencing.ist_today", return_value=tomorrow):
        res = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    next_ids = _ids(res.json()["current_set"]["items"])
    assert "v000005" not in next_ids
    assert "v000011" not in next_ids
    assert next_ids[0] == "v000013"


# --------------------------------------------------------------------------
# PRD §47 "Manual Next Set"
# --------------------------------------------------------------------------

async def test_next_set_requires_acceptance_then_allocates(client):
    await _seed_vocab(client)
    h = await _auth(client, "seq5@example.com")

    await client.get("/api/v1/communication/vocabulary/today", headers=h)

    blocked = await client.post("/api/v1/communication/vocabulary/sets/next", headers=h)
    assert blocked.status_code == 409

    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    set_id = today.json()["current_set"]["id"]
    await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/accept", headers=h)

    nxt = await client.post("/api/v1/communication/vocabulary/sets/next", headers=h)
    assert nxt.status_code == 200, nxt.text
    assert nxt.json()["set_type"] == "manual"
    assert _ids(nxt.json()["items"]) == [f"v{i:06d}" for i in range(11, 21)]

    # An unaccepted manual set must not be silently replaced by a new daily set at midnight.
    tomorrow = date.today() + timedelta(days=1)
    with patch("app.modules.communication.vocabulary.sequencing.ist_today", return_value=tomorrow):
        res = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    assert res.json()["state"] == "ACTIVE"
    assert _ids(res.json()["current_set"]["items"]) == [f"v{i:06d}" for i in range(11, 21)]


# --------------------------------------------------------------------------
# PRD §47 "User isolation"
# --------------------------------------------------------------------------

async def test_user_isolation(client):
    await _seed_vocab(client)
    ha = await _auth(client, "userA@example.com")
    hb = await _auth(client, "userB@example.com")

    ra = await client.get("/api/v1/communication/vocabulary/today", headers=ha)
    rb = await client.get("/api/v1/communication/vocabulary/today", headers=hb)
    assert _ids(ra.json()["current_set"]["items"]) == [f"v{i:06d}" for i in range(1, 11)]
    assert _ids(rb.json()["current_set"]["items"]) == [f"v{i:06d}" for i in range(1, 11)]

    set_a = ra.json()["current_set"]["id"]
    await client.post(f"/api/v1/communication/vocabulary/sets/{set_a}/items/1/change", headers=ha)

    rb2 = await client.get("/api/v1/communication/vocabulary/today", headers=hb)
    assert _ids(rb2.json()["current_set"]["items"]) == [f"v{i:06d}" for i in range(1, 11)]


# --------------------------------------------------------------------------
# PRD §47 "Reload" — refreshing must return the same active set
# --------------------------------------------------------------------------

async def test_reload_returns_same_active_set(client):
    await _seed_vocab(client)
    h = await _auth(client, "seq6@example.com")

    first = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    second = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    assert first.json()["current_set"]["id"] == second.json()["current_set"]["id"]
    assert _ids(first.json()["current_set"]["items"]) == _ids(second.json()["current_set"]["items"])


# --------------------------------------------------------------------------
# PRD §47 "Concurrency" — no two simultaneous Change requests get the same vocabulary
# --------------------------------------------------------------------------

async def test_concurrent_changes_never_allocate_duplicate_vocabulary(client):
    await _seed_vocab(client, count=40)
    h = await _auth(client, "seq7@example.com")

    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    set_id = today.json()["current_set"]["id"]

    responses = await asyncio.gather(
        *[
            client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/items/{pos}/change", headers=h)
            for pos in range(1, 6)
        ]
    )
    for r in responses:
        assert r.status_code in (200, 409)

    final = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    final_ids = _ids(final.json()["current_set"]["items"])
    assert len(final_ids) == len(set(final_ids))  # no duplicate ever allocated


# --------------------------------------------------------------------------
# PRD §53 "End of dataset" — no more items to allocate
# --------------------------------------------------------------------------

async def test_end_of_dataset_with_no_vocabulary_imported(client):
    h = await _auth(client, "seq8@example.com")  # no _seed_vocab() call — empty master dataset

    res = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    body = res.json()
    assert body["end_of_dataset"] is True
    assert body["state"] == "NO_ACTIVE_SET"
    assert body["current_set"] is None


async def test_end_of_dataset_after_full_consumption(client):
    await _seed_vocab(client, count=10)  # exactly one daily set, nothing left after
    h = await _auth(client, "seq9@example.com")

    today = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    set_id = today.json()["current_set"]["id"]
    await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/accept", headers=h)

    tomorrow = date.today() + timedelta(days=1)
    with patch("app.modules.communication.vocabulary.sequencing.ist_today", return_value=tomorrow):
        res = await client.get("/api/v1/communication/vocabulary/today", headers=h)
    body = res.json()
    assert body["end_of_dataset"] is True
    assert body["state"] == "WAITING_FOR_NEXT_MIDNIGHT"
    assert body["current_set"]["id"] == set_id  # last accepted set still returned, read-only
