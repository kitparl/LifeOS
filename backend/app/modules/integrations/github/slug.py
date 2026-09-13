"""Slug helpers for GitHub repo paths (mirrors frontend markdown-export sanitizer)."""

from __future__ import annotations

import re

# Keep letters, digits, hyphen; turn everything else into a separator.
_NON_SLUG = re.compile(r"[^a-z0-9]+")
_MULTI_HYPHEN = re.compile(r"-{2,}")
_LEADING_NUMBER = re.compile(r"^\d+-")


def slugify(title: str, fallback: str = "untitled") -> str:
    """Turn a note/chapter title into a clean path segment.

    "Variable, Types, Expressions" → variable-types-expressions
    "Data Types: Numeric and Boolean" → data-types-numeric-and-boolean
    """
    base = (title or "").strip().lower()
    base = _NON_SLUG.sub("-", base)
    base = _MULTI_HYPHEN.sub("-", base).strip("-")
    return base or fallback


def strip_leading_number(slug: str, fallback: str = "untitled") -> str:
    """Strip a leading `NN-` from a slug before applying a fresh numeric prefix.

    Guards against double-numbered-looking folders when a title itself happens to
    start with digits (e.g. a chapter titled "5 Intro" slugifies to "5-intro";
    without stripping, applying the computed rank would render as "02-5-intro").
    Only used for chapter/section slugs — subject slugs are never numbered.
    """
    stripped = _LEADING_NUMBER.sub("", slug, count=1)
    return stripped or slug or fallback
