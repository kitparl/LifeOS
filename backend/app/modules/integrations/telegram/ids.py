"""Short-id helpers — never expose full UUIDs in visible Telegram text."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def short_id(entity_id: str, length: int = 8) -> str:
    return (entity_id or "")[:length]


def match_by_prefix(items: list[T], token: str, *, id_attr: str = "id") -> list[T]:
    token = (token or "").strip().lower()
    if not token:
        return []
    matches: list[T] = []
    for item in items:
        eid = str(getattr(item, id_attr, "")).lower()
        if eid.startswith(token) or eid == token:
            matches.append(item)
    return matches


def resolve_one(items: list[T], token: str, *, id_attr: str = "id") -> T | None:
    matches = match_by_prefix(items, token, id_attr=id_attr)
    if len(matches) == 1:
        return matches[0]
    return None
