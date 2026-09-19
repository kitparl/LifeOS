"""Example-based regression tests for the JSON import pipeline (PRD §6, §43).
Complements the PBT properties in test_vocabulary_pbt.py (PBT-10)."""

import json

import pytest
from app.core.database import Base
from app.modules.communication.vocabulary.models import Vocabulary, VocabularyCollection
from app.modules.communication.vocabulary.seeder import ImportSummary, import_records, load_and_validate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

VALID_RECORD = {
    "id": "v000001",
    "term": "let's not go there",
    "type": "COMMON_EXPRESSION",
    "level": "A2",
    "part_of_speech": "expression",
    "simple_meaning": "I do not want to discuss that topic.",
    "meaning_in_context": "Used to sound natural in conversation.",
    "communication_intents": ["expressing_opinion", "clarifying"],
    "topics": ["communication", "work"],
    "example": "Let's not go there in a mixed meeting.",
    "example_context": "A conversation with colleagues.",
    "usage_note": "Sounds natural in spoken English.",
    "common_collocations": [],
    "synonyms": [],
    "antonyms": [],
    "commonness": "very_common",
    "formality": "neutral",
    "pronunciation": None,
    "learning_priority": "high",
}


def test_load_and_validate_reports_malformed_records_without_dropping_silently(tmp_path):
    data = {
        "dataset_version": "1.0",
        "language": "en",
        "items": [
            VALID_RECORD,
            {**VALID_RECORD, "id": "v000002", "term": "duplicate id test", "level": "bogus-level"},
            {**VALID_RECORD, "id": "not-an-id", "term": "bad id format"},
            {**VALID_RECORD, "id": "v000001", "term": "duplicate id of record 1"},  # dup id
        ],
    }
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    valid, summary = load_and_validate(path)

    assert summary.imported == 4
    assert len(valid) == 1
    assert valid[0]["id"] == "v000001"
    assert summary.skipped == 3
    assert len(summary.errors) == 3


@pytest.mark.asyncio
async def test_import_records_inserts_then_updates_without_renumbering():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        summary = ImportSummary(imported=1)
        await import_records(db, [VALID_RECORD], summary)
        await db.commit()
        assert summary.inserted == 1
        assert summary.updated == 0

        row = (await db.execute(select(Vocabulary).where(Vocabulary.id == "v000001"))).scalar_one()
        assert row.term == "let's not go there"
        assert row.sequence_number == 1

        collections = (await db.execute(select(VocabularyCollection))).scalars().all()
        assert len(collections) == 1
        assert collections[0].name == "Practical English Vocabulary"

    # Re-import with a corrected term (PRD §45 "corrected definitions" scenario) — content
    # updates, sequence_number (and collection) stay stable.
    updated_record = {**VALID_RECORD, "term": "let's not go there (corrected)"}
    async with session_factory() as db:
        summary2 = ImportSummary(imported=1)
        await import_records(db, [updated_record], summary2)
        await db.commit()
        assert summary2.inserted == 0
        assert summary2.updated == 1

        row = (await db.execute(select(Vocabulary).where(Vocabulary.id == "v000001"))).scalar_one()
        assert row.term == "let's not go there (corrected)"
        assert row.sequence_number == 1  # never renumbered (PRD §7)

    await engine.dispose()


@pytest.mark.asyncio
async def test_import_against_real_dataset_sample():
    """Sanity check against the actual practical-english-vocabulary.json — first 50 records."""
    from pathlib import Path

    seed_path = (
        Path(__file__).resolve().parents[2]
        / "app" / "modules" / "communication" / "vocabulary" / "seeds" / "practical-english-vocabulary.json"
    )
    if not seed_path.is_file():
        pytest.skip("seed dataset not present")

    raw = json.loads(seed_path.read_text(encoding="utf-8"))
    sample = {**raw, "items": raw["items"][:50]}
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(sample, f)
        tmp_path = f.name

    from pathlib import Path as P

    valid, summary = load_and_validate(P(tmp_path))
    assert summary.imported == 50
    assert summary.skipped == 0
    assert len(valid) == 50

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session_factory() as db:
        import_summary = ImportSummary(imported=len(valid))
        await import_records(db, valid, import_summary)
        await db.commit()
        assert import_summary.inserted == 50
    await engine.dispose()
