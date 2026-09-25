"""Map Word Lab / Word of the Day data onto `vocabulary` columns (pure functions, no I/O).

API payloads are thinner than the seeded dataset, so required columns get safe defaults.
Text is always passed through `clean_text` because it crosses a trust boundary (vendor or
browser) before being stored and later rendered.
"""

from __future__ import annotations

import re
import secrets
from datetime import date
from typing import Any

from app.modules.integrations.wordnik.client import WordOfTheDayEntry, clean_text

DEFAULT_TYPE = "WORD"
DEFAULT_LEVEL = "B1"
DEFAULT_PART_OF_SPEECH = "unknown"
DEFAULT_COMMONNESS = "common"
DEFAULT_FORMALITY = "neutral"
DEFAULT_LEARNING_PRIORITY = "medium"
MAX_SYNONYMS = 20
_WS_RE = re.compile(r"\s+")
_PART_OF_SPEECH_MAX = 32
_TERM_MAX = 200


def normalize_term(term: str) -> str:
    """Dedupe key: plain text, trimmed, lowercased, inner whitespace collapsed."""
    return _WS_RE.sub(" ", clean_text(term)).lower()


def new_saved_id() -> str:
    """`x` + 15 hex chars: fits vocabulary.id String(16) and never looks like a dataset id."""
    return "x" + secrets.token_hex(8)[:15]


def word_of_the_day_id(day: date) -> str:
    return f"w{day:%Y%m%d}"


def _placeholder_example(term: str) -> str:
    return f'Try using "{term}" in a sentence of your own.'


def vocabulary_fields(
    *,
    term: str,
    definition: str,
    part_of_speech: str | None = None,
    example: str | None = None,
    synonyms: list[str] | None = None,
    usage_note: str | None = None,
) -> dict[str, Any]:
    """Content columns for a new `vocabulary` row (id, sequence, collection, source set by caller)."""
    clean_term = clean_text(term)[:_TERM_MAX]
    clean_synonyms = [s for s in (clean_text(s) for s in synonyms or []) if s][:MAX_SYNONYMS]
    return {
        "term": clean_term,
        "type": DEFAULT_TYPE,
        "level": DEFAULT_LEVEL,
        "part_of_speech": (clean_text(part_of_speech) or DEFAULT_PART_OF_SPEECH)[:_PART_OF_SPEECH_MAX],
        "simple_meaning": clean_text(definition),
        "example": clean_text(example) or _placeholder_example(clean_term),
        "usage_note": clean_text(usage_note) or None,
        "synonyms": clean_synonyms,
        "commonness": DEFAULT_COMMONNESS,
        "formality": DEFAULT_FORMALITY,
        "learning_priority": DEFAULT_LEARNING_PRIORITY,
    }


def word_of_the_day_fields(entry: WordOfTheDayEntry) -> dict[str, Any] | None:
    """Row content for a Word of the Day entry, or None when Wordnik gave no definition."""
    if not entry.definitions:
        return None
    first = entry.definitions[0]
    return vocabulary_fields(
        term=entry.word,
        definition=first.text,
        part_of_speech=first.part_of_speech,
        example=entry.examples[0] if entry.examples else None,
        usage_note=entry.note,
    )
