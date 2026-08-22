"""Slug helpers for GitHub repo paths (mirrors frontend markdown-export sanitizer)."""

from __future__ import annotations

import re

_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def slugify(title: str, fallback: str = "untitled") -> str:
    base = (title or "").strip()
    base = _UNSAFE.sub("", base)
    base = re.sub(r"\s+", "-", base)
    base = base.strip("-") or fallback
    return base.lower()
