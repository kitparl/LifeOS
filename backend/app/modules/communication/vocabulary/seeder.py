"""Idempotent master-vocabulary importer (PRD §6, §43).

Modeled on ``app.modules.learning.seeder`` (upsert-by-stable-key, never touches fields
that would break existing user state), but simpler: this import is global, not per-user,
and reports an aggregate summary since it processes ~15,000 records at once rather than
one small per-user seed file.

Usage (run manually, once, or repeatably — never at app startup):
    python -m app.modules.communication.vocabulary.seeder [--file path/to/dataset.json]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.communication.vocabulary.models import (
    COMMONNESS,
    FORMALITY,
    LEARNING_PRIORITY,
    LEVELS,
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


async def import_records(db: AsyncSession, records: list[dict[str, Any]], summary: ImportSummary) -> None:
    dataset_version = "1.0"
    collection = await _get_or_create_collection(db, dataset_version)

    existing_ids = set(
        (await db.execute(select(Vocabulary.id))).scalars().all()
    )

    for record in records:
        rid = record["id"]
        sequence_number = int(ID_RE.match(rid).group(1))  # type: ignore[union-attr]
        fields = {
            "collection_id": collection.id,
            "sequence_number": sequence_number,
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
            "dataset_version": record.get("dataset_version", dataset_version),
        }
        if rid in existing_ids:
            row = await db.get(Vocabulary, rid)
            for k, v in fields.items():
                if k == "sequence_number":
                    continue  # never renumber an existing item (PRD §7)
                setattr(row, k, v)
            summary.updated += 1
        else:
            db.add(Vocabulary(id=rid, **fields))
            summary.inserted += 1
        await db.flush()


async def run_import(path: Path) -> ImportSummary:
    from app.core.database import async_session_factory

    records, summary = load_and_validate(path)
    async with async_session_factory() as db:
        await import_records(db, records, summary)
        await db.commit()
    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Import the master vocabulary dataset")
    parser.add_argument("--file", type=Path, default=DEFAULT_SEED_PATH, help="Path to the dataset JSON")
    args = parser.parse_args()

    if not args.file.is_file():
        logger.error("Seed file not found: %s", args.file)
        sys.exit(1)

    summary = asyncio.run(run_import(args.file))
    print(summary.report())
    if summary.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
