"""User-extensible name registries (Q&A types, wishlist categories, routine areas, shoes, ...).

Each registry is a table with ``user_id`` and ``name`` columns. The list a user sees is the
module's suggested defaults plus their own names, de-duplicated case-insensitively.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def merge_names(*groups: Iterable[str]) -> list[str]:
    """Union of name groups: first spelling wins, blanks dropped, sorted case-insensitively."""
    seen: dict[str, str] = {}
    for group in groups:
        for name in group:
            key = name.strip().lower()
            if key and key not in seen:
                seen[key] = name.strip()
    return sorted(seen.values(), key=str.lower)


async def list_names(db: AsyncSession, model: Any, user_id: str) -> list[str]:
    result = await db.execute(select(model.name).where(model.user_id == user_id).order_by(model.name.asc()))
    return list(result.scalars().all())


async def ensure_name(db: AsyncSession, model: Any, user_id: str, name: str | None) -> None:
    """Register a name for reuse (idempotent, case-insensitive)."""
    clean = (name or "").strip()
    if not clean:
        return
    existing = await list_names(db, model, user_id)
    if any(row.lower() == clean.lower() for row in existing):
        return
    db.add(model(user_id=user_id, name=clean))
    await db.flush()
