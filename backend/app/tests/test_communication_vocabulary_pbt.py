"""Property-based tests (Hypothesis) — Property-Based Testing extension, full enforcement.

Properties identified in aidlc-docs/inception/requirements/requirements-19sept-vocabulary.md
("Property-Based Testing" table). Complements (does not replace) the example-based tests in
test_vocabulary_sequencing.py — PBT-10.

These are plain (non-async) test functions: Hypothesis's shrinking loop runs the test body
many times per property, and mixing that with pytest-asyncio's per-test event loop is more
trouble than it's worth here — DB-touching properties open their own short-lived asyncio.run()
per generated example instead.
"""

import asyncio
import string

from app.core.database import Base
from app.modules.auth.models import User
from app.modules.communication.vocabulary.models import (
    COMMONNESS,
    FORMALITY,
    LEARNING_PRIORITY,
    LEVELS,
    VOCAB_TYPES,
)
from app.modules.communication.vocabulary.repository import VocabularyRepository
from app.modules.communication.vocabulary.seeder import (
    ImportSummary,
    _validate_record,
    import_records,
)
from app.modules.communication.vocabulary.sequencing import allocate_next
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# --------------------------------------------------------------------------
# Generators (PBT-07 — domain-shaped, not raw primitives)
# --------------------------------------------------------------------------

_word_text = st.text(alphabet=string.ascii_lowercase + " '-", min_size=1, max_size=40).map(str.strip).filter(bool)

valid_record = st.builds(
    lambda n, term, meaning, ex, level, typ, commonness, formality, priority: {
        "id": f"v{n:06d}",
        "term": term,
        "type": typ,
        "level": level,
        "part_of_speech": "noun",
        "simple_meaning": meaning,
        "example": ex,
        "commonness": commonness,
        "formality": formality,
        "learning_priority": priority,
        "topics": ["work"],
        "synonyms": [],
    },
    n=st.integers(min_value=1, max_value=999999),
    term=_word_text,
    meaning=_word_text,
    ex=_word_text,
    level=st.sampled_from(LEVELS),
    typ=st.sampled_from(VOCAB_TYPES),
    commonness=st.sampled_from(COMMONNESS),
    formality=st.sampled_from(FORMALITY),
    priority=st.sampled_from(LEARNING_PRIORITY),
)


# --------------------------------------------------------------------------
# PBT-03 Invariant: a structurally valid record is always accepted
# --------------------------------------------------------------------------

@given(record=valid_record)
def test_valid_record_always_passes_validation(record):
    error = _validate_record(record, seen_ids=set(), seen_terms=set())
    assert error is None


# --------------------------------------------------------------------------
# PBT-03 Invariant: corrupting any single required field always rejects the record
# --------------------------------------------------------------------------

@given(
    record=valid_record,
    field=st.sampled_from(["id", "term", "level", "type", "commonness", "formality", "learning_priority"]),
)
def test_malformed_record_is_always_rejected_never_silently_accepted(record, field):
    corrupted = dict(record)
    if field == "id":
        corrupted["id"] = "not-a-valid-id"
    elif field in ("level", "type", "commonness", "formality", "learning_priority"):
        corrupted[field] = "definitely-not-a-real-enum-value"
    else:
        del corrupted[field]
    error = _validate_record(corrupted, seen_ids=set(), seen_terms=set())
    assert error is not None


@given(record=valid_record)
def test_duplicate_id_within_file_is_rejected(record):
    seen_ids = {record["id"]}
    error = _validate_record(record, seen_ids=seen_ids, seen_terms=set())
    assert error is not None
    assert "duplicate id" in error


# --------------------------------------------------------------------------
# PBT-04 Idempotence: importing the same valid records twice never inserts twice and
# never mutates sequence_number on the second pass.
# --------------------------------------------------------------------------

async def _run_import_twice(records: list[dict]) -> tuple[ImportSummary, ImportSummary, list[int]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        summary1 = ImportSummary(imported=len(records))
        await import_records(db, records, summary1)
        await db.commit()

    async with session_factory() as db:
        summary2 = ImportSummary(imported=len(records))
        await import_records(db, records, summary2)
        await db.commit()

    async with session_factory() as db:
        from app.modules.communication.vocabulary.models import Vocabulary
        from sqlalchemy import select

        seq_numbers = (
            await db.execute(select(Vocabulary.sequence_number).order_by(Vocabulary.sequence_number))
        ).scalars().all()

    await engine.dispose()
    return summary1, summary2, list(seq_numbers)


@given(records=st.lists(valid_record, min_size=1, max_size=5, unique_by=lambda r: r["id"]))
@settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_import_is_idempotent(records):
    summary1, summary2, seq_numbers = asyncio.run(_run_import_twice(records))
    assert summary1.inserted == len(records)
    assert summary1.updated == 0
    assert summary2.inserted == 0
    assert summary2.updated == len(records)
    assert seq_numbers == sorted(seq_numbers)
    assert len(seq_numbers) == len(set(seq_numbers))  # sequence_number never duplicated by re-import


# --------------------------------------------------------------------------
# PBT-03 Invariant + PBT-06 Stateful (simplified): allocate_next never repeats a
# vocabulary id for a user, and next_sequence_number advances by exactly what was
# allocated, across an arbitrary sequence of allocation-size requests.
# --------------------------------------------------------------------------

async def _run_allocation_sequence(pool_size: int, request_sizes: list[int]) -> tuple[list[str], int, int]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    records = [
        {
            "id": f"v{i:06d}",
            "term": f"term-{i}",
            "type": "WORD",
            "level": "A2",
            "part_of_speech": "noun",
            "simple_meaning": f"meaning {i}",
            "example": f"example {i}",
            "commonness": "common",
            "formality": "neutral",
            "learning_priority": "medium",
        }
        for i in range(1, pool_size + 1)
    ]

    all_allocated: list[str] = []
    async with session_factory() as db:
        summary = ImportSummary(imported=len(records))
        await import_records(db, records, summary)

        user = User(email="pbt@example.com", username="pbt_user", hashed_password="x", display_name="PBT")
        db.add(user)
        await db.flush()

        repo = VocabularyRepository(db)
        for size in request_sizes:
            rows = await allocate_next(db, repo, user, size)
            all_allocated.extend(v.id for v in rows)
        await db.commit()

        progress = await repo.get_progress(user.id)
        final_pointer = progress.next_sequence_number if progress else 1

    await engine.dispose()
    return all_allocated, final_pointer, pool_size


@given(
    pool_size=st.integers(min_value=5, max_value=30),
    request_sizes=st.lists(st.integers(min_value=1, max_value=10), min_size=1, max_size=6),
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_allocation_never_repeats_and_pointer_matches_allocated_count(pool_size, request_sizes):
    allocated, final_pointer, _pool_size = asyncio.run(_run_allocation_sequence(pool_size, request_sizes))
    assert len(allocated) == len(set(allocated))  # PRD §62 rule 6 — never allocated twice
    assert final_pointer == 1 + len(allocated)  # pointer advances by exactly what was allocated


# --------------------------------------------------------------------------
# PBT-03 Invariant: mastery_level stays within [0, 5] across any sequence of
# correct/incorrect game/revision results (PRD §30).
# --------------------------------------------------------------------------

@given(results=st.lists(st.booleans(), min_size=0, max_size=50))
def test_mastery_level_always_stays_within_bounds(results):
    from app.modules.communication.vocabulary.mastery import MAX_MASTERY, MIN_MASTERY, next_mastery_level

    level = 0
    for is_correct in results:
        level = next_mastery_level(level, is_correct)
        assert MIN_MASTERY <= level <= MAX_MASTERY


@given(start=st.integers(min_value=0, max_value=5))
def test_mastery_level_idempotent_boundaries(start):
    from app.modules.communication.vocabulary.mastery import next_mastery_level

    # Repeatedly wrong from any starting point converges to and stays at the floor.
    level = start
    for _ in range(10):
        level = next_mastery_level(level, False)
    assert level == 0

    # Repeatedly correct from any starting point converges to and stays at the ceiling.
    level = start
    for _ in range(10):
        level = next_mastery_level(level, True)
    assert level == 5
