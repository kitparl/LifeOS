"""Idempotent master-vocabulary importer (PRD §6, §43).

Upsert-by-stable-key; never touches fields that would break existing user state.
The import is global, not per-user, and reports an aggregate summary since it processes ~15,000 records at once rather than
one small per-user seed file.

Usage (run from the backend/ directory, never at app startup):
    cd backend
    python -m app.modules.communication.vocabulary.seeder
    python -m app.modules.communication.vocabulary.seeder --file /absolute/path/to/dataset.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.communication.vocabulary.models import (
    COMMONNESS,
    FORMALITY,
    LEARNING_PRIORITY,
    LEVELS,
    SOURCE_DATASET,
    VOCAB_TYPES,
    Vocabulary,
    VocabularyCollection,
)

logger = logging.getLogger(__name__)

DEFAULT_SEED_PATH = Path(__file__).resolve().parent / "seeds" / "practical-english-vocabulary.json"
ID_RE = re.compile(r"^v(\d{6})$")
DEFAULT_COLLECTION_NAME = "Practical English Vocabulary"

REQUIRED_STR_FIELDS = (
    "id",
    "term",
    "type",
    "level",
    "part_of_speech",
    "simple_meaning",
    "example",
    "commonness",
    "formality",
    "learning_priority",
)
LIST_FIELDS = ("communication_intents", "topics", "common_collocations", "synonyms", "antonyms")
BATCH_SIZE = 200
# Content columns refreshed on re-import. sequence_number / created_at stay frozen (PRD §7).
_UPSERT_UPDATE_COLUMNS = (
    "collection_id",
    "term",
    "type",
    "level",
    "part_of_speech",
    "simple_meaning",
    "meaning_in_context",
    "communication_intents",
    "topics",
    "example",
    "example_context",
    "usage_note",
    "common_collocations",
    "synonyms",
    "antonyms",
    "commonness",
    "formality",
    "pronunciation",
    "learning_priority",
    "updated_at",
    "dataset_version",
)


class SeedValidationError(ValueError):
    pass


@dataclass
class ImportSummary:
    imported: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def report(self) -> str:
        lines = [
            f"Imported: {self.imported}",
            f"Inserted: {self.inserted}",
            f"Updated: {self.updated}",
            f"Skipped: {self.skipped}",
            f"Errors: {len(self.errors)}",
        ]
        if self.errors:
            lines.append("")
            lines.append("Error detail:")
            lines.extend(f"  - {e}" for e in self.errors)
        return "\n".join(lines)


def _validate_record(record: dict[str, Any], seen_ids: set[str], seen_terms: set[str]) -> str | None:
    """Return an error message, or None if the record is valid."""
    for f in REQUIRED_STR_FIELDS:
        if not isinstance(record.get(f), str) or not record[f]:
            return f"missing/invalid required field {f!r}"
    for f in LIST_FIELDS:
        if f in record and not isinstance(record[f], list):
            return f"field {f!r} must be a list"

    rid = record["id"]
    match = ID_RE.match(rid)
    if not match:
        return f"id {rid!r} does not match ^v\\d{{6}}$"
    if rid in seen_ids:
        return f"duplicate id {rid!r} within import file"

    term = record["term"]
    if term in seen_terms:
        return f"duplicate term {term!r} within import file"

    if record["level"] not in LEVELS:
        return f"level {record['level']!r} not in {LEVELS}"
    if record["type"] not in VOCAB_TYPES:
        return f"type {record['type']!r} not in {VOCAB_TYPES}"
    if record["commonness"] not in COMMONNESS:
        return f"commonness {record['commonness']!r} not in {COMMONNESS}"
    if record["formality"] not in FORMALITY:
        return f"formality {record['formality']!r} not in {FORMALITY}"
    if record["learning_priority"] not in LEARNING_PRIORITY:
        return f"learning_priority {record['learning_priority']!r} not in {LEARNING_PRIORITY}"

    return None


def load_and_validate(path: Path) -> tuple[list[dict[str, Any]], ImportSummary]:
    """Read + validate every record. Malformed records are reported, never silently
    dropped (PRD §6.10) — they're excluded from the returned valid-record list and
    counted in ``summary.skipped``/``summary.errors``."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("items") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise SeedValidationError("Seed file must contain a top-level 'items' list")

    summary = ImportSummary(imported=len(items))
    valid: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_terms: set[str] = set()

    for idx, record in enumerate(items):
        if not isinstance(record, dict):
            summary.errors.append(f"record #{idx}: not an object")
            summary.skipped += 1
            continue
        error = _validate_record(record, seen_ids, seen_terms)
        if error:
            rid = record.get("id", f"#{idx}")
            summary.errors.append(f"{rid}: {error}")
            summary.skipped += 1
            continue
        seen_ids.add(record["id"])
        seen_terms.add(record["term"])
        valid.append(record)

    return valid, summary


async def _get_or_create_collection(db: AsyncSession, dataset_version: str) -> VocabularyCollection:
    result = await db.execute(
        select(VocabularyCollection).where(VocabularyCollection.name == DEFAULT_COLLECTION_NAME)
    )
    collection = result.scalar_one_or_none()
    if collection is None:
        collection = VocabularyCollection(
            name=DEFAULT_COLLECTION_NAME,
            description="Practical everyday English vocabulary",
            language="en",
            version=dataset_version,
            status="active",
        )
        db.add(collection)
        await db.flush()
    return collection


def _dialect_name(db: AsyncSession) -> str:
    bind = db.bind
    if bind is None:
        bind = db.sync_session.get_bind()
    return bind.dialect.name


def _row_from_record(record: dict[str, Any], collection_id: str, dataset_version: str) -> dict[str, Any]:
    rid = record["id"]
    now = datetime.now(timezone.utc)
    return {
        "id": rid,
        "collection_id": collection_id,
        "sequence_number": int(ID_RE.match(rid).group(1)),  # type: ignore[union-attr]
        "term": record["term"],
        "type": record["type"],
        "level": record["level"],
        "part_of_speech": record["part_of_speech"],
        "simple_meaning": record["simple_meaning"],
        "meaning_in_context": record.get("meaning_in_context"),
        "communication_intents": record.get("communication_intents", []),
        "topics": record.get("topics", []),
        "example": record["example"],
        "example_context": record.get("example_context"),
        "usage_note": record.get("usage_note"),
        "common_collocations": record.get("common_collocations", []),
        "synonyms": record.get("synonyms", []),
        "antonyms": record.get("antonyms", []),
        "commonness": record["commonness"],
        "formality": record["formality"],
        "pronunciation": record.get("pronunciation"),
        "learning_priority": record["learning_priority"],
        "created_at": now,
        "updated_at": now,
        "dataset_version": record.get("dataset_version", dataset_version),
        "source": SOURCE_DATASET,
        "exclude_from_daily": False,
    }


def _upsert_stmt(dialect_name: str, rows: list[dict[str, Any]]):
    if dialect_name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as dialect_insert
    else:
        from sqlalchemy.dialects.sqlite import insert as dialect_insert

    stmt = dialect_insert(Vocabulary).values(rows)
    return stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={col: stmt.excluded[col] for col in _UPSERT_UPDATE_COLUMNS},
    )


async def import_records(
    db: AsyncSession,
    records: list[dict[str, Any]],
    summary: ImportSummary,
    *,
    commit_batches: bool = False,
) -> None:
    dataset_version = "1.0"
    collection = await _get_or_create_collection(db, dataset_version)

    existing_ids = set((await db.execute(select(Vocabulary.id))).scalars().all())
    rows = [_row_from_record(record, collection.id, dataset_version) for record in records]
    for row in rows:
        if row["id"] in existing_ids:
            summary.updated += 1
        else:
            summary.inserted += 1

    if commit_batches:
        await db.commit()

    dialect = _dialect_name(db)
    total = len(rows)
    for start in range(0, total, BATCH_SIZE):
        batch = rows[start : start + BATCH_SIZE]
        try:
            await db.execute(_upsert_stmt(dialect, batch))
        except ValueError as exc:
            if "not enough values to unpack" not in str(exc):
                raise
            raise RuntimeError(
                "Postgres closed the connection mid-import (asyncpg protocol error). "
                "Re-run the seeder from backend/; it is idempotent and will resume."
            ) from exc
        if commit_batches:
            await db.commit()
        else:
            await db.flush()
        done = min(start + BATCH_SIZE, total)
        logger.info("Upserted %s / %s vocabulary rows", done, total)


async def _ensure_vocabulary_tables(engine) -> None:
    """Create only vocabulary tables. Do not run full schema bootstrap — that
    imports every module's mappers (and can fail if a cross-module relationship
    is not loaded, e.g. RoutineBlock -> Habit)."""
    from app.core.database import Base
    from app.modules.communication.vocabulary.models import (
        GameQuestion,
        GameSession,
        UserVocabulary,
        UserVocabularyExample,
        UserVocabularyProgress,
        Vocabulary,
        VocabularyBookmark,
        VocabularyCollection,
        VocabularySet,
        VocabularySetItem,
    )

    tables = [
        VocabularyCollection.__table__,
        Vocabulary.__table__,
        VocabularySet.__table__,
        UserVocabularyProgress.__table__,
        VocabularySetItem.__table__,
        UserVocabulary.__table__,
        VocabularyBookmark.__table__,
        UserVocabularyExample.__table__,
        GameSession.__table__,
        GameQuestion.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))


async def run_import(path: Path) -> ImportSummary:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.core.config import get_settings

    settings = get_settings()
    connect_args: dict[str, Any] = {}
    if "asyncpg" in settings.database_url:
        # Prepared-statement cache + a 15k-row ORM flush loop is what surfaces
        # asyncpg's "expected 3, got 0" unpack error when the server/proxy
        # drops the connection. Disable the cache for this CLI process.
        connect_args = {"statement_cache_size": 0, "timeout": 120}

    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=1,
        connect_args=connect_args,
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    records, summary = load_and_validate(path)
    logger.info(
        "Validated %s records (%s skipped, %s errors)",
        len(records),
        summary.skipped,
        len(summary.errors),
    )
    try:
        await _ensure_vocabulary_tables(engine)
        async with session_factory() as db:
            await import_records(db, records, summary, commit_batches=True)
    finally:
        await engine.dispose()
    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(
        description="Import the master vocabulary dataset (run from the backend/ directory)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_SEED_PATH,
        help="Path to the dataset JSON (defaults to the bundled 15,000-item file)",
    )
    args = parser.parse_args()

    if not args.file.is_file():
        logger.error("Seed file not found: %s", args.file)
        logger.error("Run from backend/: python -m app.modules.communication.vocabulary.seeder")
        sys.exit(1)

    summary = asyncio.run(run_import(args.file))
    print(summary.report())
    if summary.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
