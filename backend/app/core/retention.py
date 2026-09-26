"""Hard-delete rows whose soft-delete/archive timestamp is older than a retention window."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezone import utc_now


async def purge_older_than(db: AsyncSession, model: Any, column: Any, days: int, *criteria: Any) -> list[Any]:
    """Delete rows of ``model`` whose ``column`` is set and older than ``days``. Returns the deleted rows."""
    cutoff = utc_now() - timedelta(days=days)
    result = await db.execute(select(model).where(column.is_not(None), column < cutoff, *criteria))
    rows = list(result.scalars().all())
    for row in rows:
        await db.delete(row)
    if rows:
        await db.flush()
    return rows
