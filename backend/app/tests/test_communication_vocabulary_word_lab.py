"""Word Lab + Word of the Day: sequencing safety, lookups, games, save, and the WotD cache cascade.
All Wordnik HTTP is mocked (see the `wordnik` fixture in conftest.py)."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

from app.core.timezone import ist_today
from app.modules.communication.vocabulary.models import (
    RESERVED_SEQUENCE_START,
    SOURCE_API,
    SOURCE_USER_SAVED,
    Vocabulary,
    VocabularyCollection,
)
from app.modules.communication.vocabulary.repository import VocabularyRepository
from app.modules.communication.vocabulary.wordnik_mapper import (
    new_saved_id,
    normalize_term,
    vocabulary_fields,
    word_of_the_day_id,
)

API = "/api/v1"
VOCAB = f"{API}/communication/vocabulary"
KEY = "wordnik-secret-key-1234"


async def _auth(client, email: str) -> dict[str, str]:
    reg = await client.post(
        f"{API}/auth/register",
        json={
            "username": "usr_" + email.split("@")[0].replace(".", "")[:26],
            "email": email,
            "password": "password123",
            "display_name": "Word Lab",
        },
    )
    assert reg.status_code in (200, 201), reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


async def _connect(client, headers) -> None:
    res = await client.put(f"{API}/integrations/wordnik/config", headers=headers, json={"api_key": KEY})
    assert res.status_code == 200, res.text


def _vocab_row(collection_id: str, seq: int, term: str, **extra) -> Vocabulary:
    return Vocabulary(
        id=extra.pop("id", f"v{seq:06d}"),
        collection_id=collection_id,
        sequence_number=seq,
        term=term,
        type="WORD",
        level="A2",
        part_of_speech="noun",
        simple_meaning=f"meaning of {term}",
        example=f"example with {term}",
        commonness="common",
        formality="neutral",
        learning_priority="medium",
        **extra,
    )


async def _seed(client, count: int, *extra_rows: dict) -> None:
    """`count` dataset rows v000001.., plus extra rows given as _vocab_row kwargs."""
    async with client.session_factory() as db:
        collection = VocabularyCollection(name="Test Collection", language="en", version="1.0", status="active")
        db.add(collection)
        await db.flush()
        for i in range(1, count + 1):
            db.add(_vocab_row(collection.id, i, f"word-{i}"))
        for row in extra_rows:
            db.add(_vocab_row(collection.id, **row))
        await db.commit()


# ---------------------------------------------------------------------------
# Sequencing safety: non-dataset rows are never allocated nor counted
# ---------------------------------------------------------------------------


async def test_flagged_rows_after_the_dataset_are_never_allocated(client):
    saved = {
        "id": "xsaved000000001",
        "seq": RESERVED_SEQUENCE_START,
        "term": "saved-word",
        "source": SOURCE_USER_SAVED,
        "exclude_from_daily": True,
    }
    await _seed(client, 12, saved)
    h = await _auth(client, "wlseq@example.com")

    first = (await client.get(f"{VOCAB}/today", headers=h)).json()
    await client.post(f"{VOCAB}/sets/{first['current_set']['id']}/accept", headers=h)
    # Only 2 dataset words are left; the flagged row must not top up the next set.
    nxt = await client.post(f"{VOCAB}/sets/next", headers=h)
    assert nxt.status_code == 200, nxt.text
    ids = [it["vocabulary"]["id"] for it in nxt.json()["items"]]
    assert ids == ["v000011", "v000012"]

    # Dataset exhausted: another Next Set finds nothing (the flagged row is still ineligible).
    await client.post(f"{VOCAB}/sets/{nxt.json()['id']}/accept", headers=h)
    again = await client.post(f"{VOCAB}/sets/next", headers=h)
    assert "xsaved000000001" not in again.text


async def test_progress_denominator_counts_only_daily_eligible_rows(client):
    await _seed(
        client,
        5,
        {"id": "w20260925", "seq": RESERVED_SEQUENCE_START, "term": "herald", "exclude_from_daily": True},
    )
    h = await _auth(client, "wlprog@example.com")
    progress = (await client.get(f"{VOCAB}/progress", headers=h)).json()
    assert progress["total_available_vocabulary"] == 5


# ---------------------------------------------------------------------------
# Mapper (pure)
# ---------------------------------------------------------------------------


def test_mapper_defaults_ids_and_cleaning():
    fields = vocabulary_fields(term="  <b>Herald</b> ", definition="A <xref>messenger</xref> &amp; envoy.")
    assert fields["term"] == "Herald"
    assert fields["simple_meaning"] == "A messenger & envoy."
    assert fields["part_of_speech"] == "unknown"
    assert fields["level"] == "B1"
    assert "Herald" in fields["example"]
    assert normalize_term("  Take   OFF ") == "take off"
    assert word_of_the_day_id(date(2026, 9, 25)) == "w20260925"
    saved_id = new_saved_id()
    assert saved_id.startswith("x") and len(saved_id) == 16


# ---------------------------------------------------------------------------
# Status / lookup
# ---------------------------------------------------------------------------


async def test_lookup_without_key_is_missing_credential_and_calls_nothing(client, wordnik):
    h = await _auth(client, "wlnokey@example.com")
    status = (await client.get(f"{VOCAB}/word-lab/status", headers=h)).json()
    assert status == {"connected": False, "usage_remaining_pct": None}

    res = await client.get(f"{VOCAB}/word-lab/lookup", params={"q": "herald"}, headers=h)
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "missing_credential"
    assert wordnik.requests == []


async def test_dictionary_lookup_returns_clean_definitions_and_usage(client, wordnik):
    h = await _auth(client, "wldict@example.com")
    await _connect(client, h)

    res = await client.get(f"{VOCAB}/word-lab/lookup", params={"q": " herald ", "mode": "dictionary"}, headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["query"] == "herald"
    assert body["definitions"] == [{"part_of_speech": "noun", "text": "A short meaning."}]
    assert body["example"] == "An example sentence."
    assert body["usage_remaining_pct"] == 73
    assert [p.rsplit("/", 1)[-1] for p in wordnik.paths()] == ["definitions", "topExample"]

    status = (await client.get(f"{VOCAB}/word-lab/status", headers=h)).json()
    assert status == {"connected": True, "usage_remaining_pct": 73}


async def test_related_word_modes(client, wordnik):
    h = await _auth(client, "wlrel@example.com")
    await _connect(client, h)

    async def words(mode: str) -> list[dict]:
        res = await client.get(f"{VOCAB}/word-lab/lookup", params={"q": "herald", "mode": mode}, headers=h)
        assert res.status_code == 200, res.text
        return res.json()["words"]

    assert [w["word"] for w in await words("synonyms")] == ["envoy", "courier"]
    assert [w["word"] for w in await words("rhymes")] == ["emerald"]
    assert await words("explorer") == [{"word": "acrophobia", "hint": "fear of heights"}]


async def test_unknown_mode_is_rejected(client):
    h = await _auth(client, "wlmode@example.com")
    res = await client.get(f"{VOCAB}/word-lab/lookup", params={"q": "herald", "mode": "spelling"}, headers=h)
    assert res.status_code == 422


async def test_rate_limit_maps_to_rate_limit_code_and_zero_usage(client, wordnik):
    h = await _auth(client, "wlrate@example.com")
    await _connect(client, h)
    wordnik.status = 429
    wordnik.usage = (5, 100)

    res = await client.get(f"{VOCAB}/word-lab/lookup", params={"q": "herald"}, headers=h)
    assert res.status_code == 503
    assert res.json()["detail"]["code"] == "rate_limit"
    status = (await client.get(f"{VOCAB}/word-lab/status", headers=h)).json()
    assert status["usage_remaining_pct"] == 0


async def test_invalid_key_is_400_not_401(client, wordnik):
    h = await _auth(client, "wlbadkey@example.com")
    await _connect(client, h)
    wordnik.status = 401

    res = await client.get(f"{VOCAB}/word-lab/lookup", params={"q": "herald"}, headers=h)
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "invalid_credential"
    assert KEY not in res.text


# ---------------------------------------------------------------------------
# Games
# ---------------------------------------------------------------------------


async def test_each_game_type_returns_a_playable_round(client, wordnik):
    h = await _auth(client, "wlgame@example.com")
    await _connect(client, h)

    guess_word = (await client.get(f"{VOCAB}/word-lab/game", params={"type": "guess_word"}, headers=h)).json()
    assert guess_word["options"] == ["alpha", "bravo", "charlie", "delta"]
    assert 0 <= guess_word["answer_index"] < 4
    assert guess_word["prompt"] == "A short meaning."

    guess_meaning = (await client.get(f"{VOCAB}/word-lab/game", params={"type": "guess_meaning"}, headers=h)).json()
    assert len(guess_meaning["options"]) == 4
    assert guess_meaning["prompt"] in ("alpha", "bravo", "charlie", "delta")

    scramble = (await client.get(f"{VOCAB}/word-lab/game", params={"type": "scramble"}, headers=h)).json()
    assert scramble["answer"] == "puzzle"
    assert sorted(scramble["prompt"]) == sorted("puzzle")
    assert scramble["prompt"] != "puzzle"
    assert scramble["hint"] == "A short meaning."


async def test_game_without_definitions_retries_once_then_fails(client, wordnik):
    h = await _auth(client, "wlgamefail@example.com")
    await _connect(client, h)
    wordnik.responses["/definitions"] = []

    res = await client.get(f"{VOCAB}/word-lab/game", params={"type": "scramble"}, headers=h)
    assert res.status_code == 503
    assert wordnik.paths().count("/v4/words.json/randomWord") == 2


# ---------------------------------------------------------------------------
# Save as vocabulary
# ---------------------------------------------------------------------------


async def test_save_creates_flagged_row_that_opens_in_detail(client, wordnik):
    await _seed(client, 3)
    h = await _auth(client, "wlsave@example.com")
    await _connect(client, h)

    res = await client.post(
        f"{VOCAB}/word-lab/save",
        headers=h,
        json={"term": "Herald", "definition": "A <i>messenger</i>.", "part_of_speech": "noun", "synonyms": ["envoy"]},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["created"] is True
    assert body["id"].startswith("x")

    detail = (await client.get(f"{VOCAB}/{body['id']}", headers=h)).json()
    assert detail["vocabulary"]["simple_meaning"] == "A messenger."
    assert detail["vocabulary"]["synonyms"] == ["envoy"]

    async with client.session_factory() as db:
        row = await db.get(Vocabulary, body["id"])
        assert row.source == SOURCE_USER_SAVED
        assert row.exclude_from_daily is True
        assert row.sequence_number >= RESERVED_SEQUENCE_START

    library = (await client.get(f"{VOCAB}/search", params={"q": "herald"}, headers=h)).json()
    assert body["id"] in [item["id"] for item in library["items"]]


async def test_save_is_idempotent_on_normalized_term(client, wordnik):
    await _seed(client, 3)
    h = await _auth(client, "wldedupe@example.com")
    await _connect(client, h)

    existing = await client.post(f"{VOCAB}/word-lab/save", headers=h, json={"term": " WORD-2 ", "definition": "x"})
    assert existing.json() == {"id": "v000002", "created": False}

    first = (await client.post(f"{VOCAB}/word-lab/save", headers=h, json={"term": "herald", "definition": "x"})).json()
    again = (await client.post(f"{VOCAB}/word-lab/save", headers=h, json={"term": "HERALD", "definition": "y"})).json()
    assert again == {"id": first["id"], "created": False}


async def test_save_validates_bounds_and_requires_connection(client, wordnik):
    await _seed(client, 1)
    h = await _auth(client, "wlbounds@example.com")

    locked = await client.post(f"{VOCAB}/word-lab/save", headers=h, json={"term": "herald", "definition": "x"})
    assert locked.status_code == 400
    assert locked.json()["detail"]["code"] == "missing_credential"

    await _connect(client, h)
    too_long = await client.post(f"{VOCAB}/word-lab/save", headers=h, json={"term": "a" * 201, "definition": "x"})
    assert too_long.status_code == 422
    tags_only = await client.post(f"{VOCAB}/word-lab/save", headers=h, json={"term": "<b></b>", "definition": "x"})
    assert tags_only.status_code == 422


# ---------------------------------------------------------------------------
# Word of the Day
# ---------------------------------------------------------------------------


def _wotd_calls(wordnik) -> int:
    return wordnik.paths().count("/v4/words.json/wordOfTheDay")


async def test_wotd_fetches_once_then_serves_from_db(client, wordnik):
    await _seed(client, 3)
    alice = await _auth(client, "wlwotda@example.com")
    bob = await _auth(client, "wlwotdb@example.com")
    await _connect(client, alice)
    await _connect(client, bob)

    first = (await client.get(f"{VOCAB}/word-of-the-day", headers=alice)).json()
    assert first["connected"] is True
    assert first["date"] == ist_today().isoformat()
    vocab = first["vocabulary"]
    assert vocab["id"] == word_of_the_day_id(ist_today())
    assert vocab["term"] == "herald"
    assert vocab["simple_meaning"] == "A messenger bearing news."
    assert vocab["example"] == "The herald announced the king."
    assert vocab["usage_note"] == "From Old French."

    second = (await client.get(f"{VOCAB}/word-of-the-day", headers=bob)).json()
    assert second["vocabulary"]["id"] == vocab["id"]
    assert _wotd_calls(wordnik) == 1

    async with client.session_factory() as db:
        row = await db.get(Vocabulary, vocab["id"])
        assert row.source == SOURCE_API
        assert row.exclude_from_daily is True
        assert row.wotd_for_date == ist_today()


async def test_wotd_requires_the_callers_own_key(client, wordnik):
    await _seed(client, 1)
    alice = await _auth(client, "wlwotdkey@example.com")
    stranger = await _auth(client, "wlwotdnone@example.com")
    await _connect(client, alice)
    await client.get(f"{VOCAB}/word-of-the-day", headers=alice)

    res = (await client.get(f"{VOCAB}/word-of-the-day", headers=stranger)).json()
    assert res["connected"] is False
    assert res["vocabulary"] is None
    assert _wotd_calls(wordnik) == 1


async def test_wotd_reuses_an_existing_row_for_the_same_term(client, wordnik):
    await _seed(client, 2, {"seq": 3, "term": "Herald"})
    h = await _auth(client, "wlwotdreuse@example.com")
    await _connect(client, h)

    res = (await client.get(f"{VOCAB}/word-of-the-day", headers=h)).json()
    assert res["vocabulary"]["id"] == "v000003"
    assert res["vocabulary"]["simple_meaning"] == "meaning of Herald"  # seeded content untouched
    async with client.session_factory() as db:
        assert await db.get(Vocabulary, word_of_the_day_id(ist_today())) is None
        seeded = await db.get(Vocabulary, "v000003")
        assert seeded.wotd_for_date == ist_today()
        assert seeded.exclude_from_daily is False


async def test_wotd_vendor_failure_caches_nothing_and_retries_next_time(client, wordnik):
    await _seed(client, 1)
    h = await _auth(client, "wlwotdfail@example.com")
    await _connect(client, h)
    wordnik.status = 503

    failed = (await client.get(f"{VOCAB}/word-of-the-day", headers=h)).json()
    assert failed == {"connected": True, "date": ist_today().isoformat(), "vocabulary": None}

    wordnik.status = None
    ok = (await client.get(f"{VOCAB}/word-of-the-day", headers=h)).json()
    assert ok["vocabulary"]["term"] == "herald"
    assert _wotd_calls(wordnik) == 2


async def test_wotd_race_serves_the_row_stored_by_the_other_request(client, wordnik):
    today = ist_today()
    await _seed(
        client,
        1,
        {"id": word_of_the_day_id(today), "seq": RESERVED_SEQUENCE_START, "term": "other", "wotd_for_date": today},
    )
    h = await _auth(client, "wlwotdrace@example.com")
    await _connect(client, h)

    real_lookup = VocabularyRepository.get_word_of_the_day
    calls = {"n": 0}

    async def miss_first_time(self, day):
        calls["n"] += 1
        return None if calls["n"] == 1 else await real_lookup(self, day)

    with patch.object(VocabularyRepository, "get_word_of_the_day", miss_first_time):
        res = await client.get(f"{VOCAB}/word-of-the-day", headers=h)
    assert res.status_code == 200, res.text
    assert res.json()["vocabulary"]["term"] == "other"
