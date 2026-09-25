"""Text helpers for strings that cross a trust boundary (vendor responses, user input)."""

from __future__ import annotations

import html
import re
from typing import Any

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def clean_text(value: Any) -> str:
    """Plain text from vendor/user markup: tags removed, entities decoded, whitespace collapsed."""
    if value is None:
        return ""
    text = html.unescape(_TAG_RE.sub("", str(value)))
    return _WS_RE.sub(" ", text).strip()
