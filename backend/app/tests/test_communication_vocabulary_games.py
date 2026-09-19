"""Stage 3 — games (PRD §28-30). Games reuse learned vocabulary and must never
advance next_sequence_number (PRD §47 "Game" test; §62 rule 12)."""

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
                    level="A2",
                    part_of_speech="noun",
                    simple_meaning=f"meaning {i}",
                    example=f"example sentence {i}",
                    commonness="common",
                    formality="neutral",
                    learning_priority="medium",
                    synonyms=[f"syn-{i}"],
                    antonyms=[f"ant-{i}"],
                )
            )
        await db.commit()


async def _accept_first_set(client, headers):
    today = await client.get("/api/v1/communication/vocabulary/today", headers=headers)
    set_id = today.json()["current_set"]["id"]
    await client.post(f"/api/v1/communication/vocabulary/sets/{set_id}/accept", headers=headers)


async def test_game_vocabulary_sources(client):
    await _seed_vocab(client)
    h = await _auth(client, "game1@example.com")
    await _accept_first_set(client, h)
    await client.post("/api/v1/communication/vocabulary/bookmarks/v000002", headers=h)

    all_learned = await client.get("/api/v1/communication/vocabulary/games/vocabulary?source=all_learned", headers=h)
    assert all_learned.status_code == 200, all_learned.text
    assert all_learned.json()["total"] == 10
    assert all_learned.json()["items"][0]["synonyms"] == ["syn-1"]

    bookmarked = await client.get("/api/v1/communication/vocabulary/games/vocabulary?source=bookmarked", headers=h)
    assert bookmarked.json()["total"] == 1
    assert bookmarked.json()["items"][0]["id"] == "v000002"

    today_source = await client.get("/api/v1/communication/vocabulary/games/vocabulary?source=today", headers=h)
    assert today_source.json()["total"] == 10

    unknown = await client.get("/api/v1/communication/vocabulary/games/vocabulary?source=nonsense", headers=h)
    assert unknown.status_code == 400


async def test_full_game_session_flow_never_advances_sequence(client):
    await _seed_vocab(client)
    h = await _auth(client, "game2@example.com")
    await _accept_first_set(client, h)

    created = await client.post(
        "/api/v1/communication/vocabulary/games/sessions",
        headers=h,
        json={"game_type": "meaning_quiz", "source": "all_learned", "total_questions": 3},
    )
    assert created.status_code == 200, created.text
    session_id = created.json()["id"]
    assert created.json()["score"] == 0
    assert created.json()["completed_at"] is None

    a1 = await client.post(
        f"/api/v1/communication/vocabulary/games/sessions/{session_id}/answers",
        headers=h,
        json={"vocabulary_id": "v000001", "question_type": "meaning_quiz", "is_correct": True},
    )
    assert a1.status_code == 200, a1.text
    assert a1.json()["is_correct"] is True
    assert a1.json()["mastery_level"] == 1  # 0 -> 1 on first correct answer

    a2 = await client.post(
        f"/api/v1/communication/vocabulary/games/sessions/{session_id}/answers",
        headers=h,
        json={"vocabulary_id": "v000002", "question_type": "meaning_quiz", "is_correct": False},
    )
    assert a2.json()["mastery_level"] == 0  # 0 -> floors at 0, never negative

    completed = await client.post(f"/api/v1/communication/vocabulary/games/sessions/{session_id}/complete", headers=h)
    assert completed.status_code == 200
    assert completed.json()["score"] == 1  # only the correct answer counted
    assert completed.json()["completed_at"] is not None

    # sequence untouched by any of this
    next_set = await client.post("/api/v1/communication/vocabulary/sets/next", headers=h)
    ids = [it["vocabulary"]["id"] for it in next_set.json()["items"]]
    assert ids[0] == "v000011"


async def test_cannot_answer_a_completed_session(client):
    await _seed_vocab(client)
    h = await _auth(client, "game3@example.com")
    await _accept_first_set(client, h)

    created = await client.post(
        "/api/v1/communication/vocabulary/games/sessions",
        headers=h,
        json={"game_type": "word_matching", "source": "all_learned", "total_questions": 1},
    )
    session_id = created.json()["id"]
    await client.post(f"/api/v1/communication/vocabulary/games/sessions/{session_id}/complete", headers=h)

    blocked = await client.post(
        f"/api/v1/communication/vocabulary/games/sessions/{session_id}/answers",
        headers=h,
        json={"vocabulary_id": "v000001", "question_type": "word_matching", "is_correct": True},
    )
    assert blocked.status_code == 409


async def test_cannot_access_another_users_game_session(client):
    await _seed_vocab(client)
    ha = await _auth(client, "gameA@example.com")
    hb = await _auth(client, "gameB@example.com")
    await _accept_first_set(client, ha)
    await _accept_first_set(client, hb)

    created = await client.post(
        "/api/v1/communication/vocabulary/games/sessions",
        headers=ha,
        json={"game_type": "fill_in_blank", "source": "all_learned", "total_questions": 1},
    )
    session_id = created.json()["id"]

    blocked = await client.post(
        f"/api/v1/communication/vocabulary/games/sessions/{session_id}/answers",
        headers=hb,
        json={"vocabulary_id": "v000001", "question_type": "fill_in_blank", "is_correct": True},
    )
    assert blocked.status_code == 404


async def test_game_history_lists_only_completed_sessions(client):
    await _seed_vocab(client)
    h = await _auth(client, "game4@example.com")
    await _accept_first_set(client, h)

    created = await client.post(
        "/api/v1/communication/vocabulary/games/sessions",
        headers=h,
        json={"game_type": "meaning_matching", "source": "all_learned", "total_questions": 1},
    )
    session_id = created.json()["id"]

    empty_history = await client.get("/api/v1/communication/vocabulary/games/history", headers=h)
    assert empty_history.json()["total"] == 0  # not completed yet

    await client.post(f"/api/v1/communication/vocabulary/games/sessions/{session_id}/complete", headers=h)

    history = await client.get("/api/v1/communication/vocabulary/games/history", headers=h)
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["game_type"] == "meaning_matching"
