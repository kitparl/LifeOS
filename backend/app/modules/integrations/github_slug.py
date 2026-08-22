"""Slug helpers for GitHub repo paths (mirrors frontend markdown-export sanitizer)."""

from __future__ import annotations

import re

# Keep letters, digits, hyphen; turn everything else into a separator.
_NON_SLUG = re.compile(r"[^a-z0-9]+")
_MULTI_HYPHEN = re.compile(r"-{2,}")


def slugify(title: str, fallback: str = "untitled") -> str:
    """Turn a note/chapter title into a clean path segment.

    "Variable, Types, Expressions" → variable-types-expressions
    "Data Types: Numeric and Boolean" → data-types-numeric-and-boolean
    """
    base = (title or "").strip().lower()
    base = _NON_SLUG.sub("-", base)
    base = _MULTI_HYPHEN.sub("-", base).strip("-")
    return base or fallback
