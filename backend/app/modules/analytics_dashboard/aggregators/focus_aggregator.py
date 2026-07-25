"""Planned focus / deep-work hours from routine templates."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.analytics_dashboard.aggregators import utc_today, window_start
from app.modules.routines.models import Routine

DEEP_WORK_AREAS = frozenset({"dsa", "learning", "book"})


def _block_hours(start, end) -> float:
    """Duration in hours; handles overnight blocks."""
    s = datetime.combine(utc_today(), start)
    e = datetime.combine(utc_today(), end)
    if e <= s:
        e += timedelta(days=1)
    return max((e - s).total_seconds() / 3600.0, 0.0)


async def planned_focus_hours(
    db: AsyncSession, user_id: str, range_days: int
) -> tuple[float, float]:
    """
    Return (focus_hours, deep_work_hours) as planned hours over the window.

    Sums block durations for each scheduled weekday occurrence in the range,
    skipping dates in skip_dates and respecting start_date/end_date.
    """
    result = await db.execute(
        select(Routine)
        .where(Routine.user_id == user_id, Routine.is_active.is_(True))
        .options(selectinload(Routine.blocks))
    )
    routines = list(result.scalars().all())
    if not routines:
        return 0.0, 0.0

    today = utc_today()
    start = window_start(range_days, today)
    focus = 0.0
    deep = 0.0

    cursor = start
    while cursor <= today:
        for routine in routines:
            if routine.start_date and cursor < routine.start_date:
                continue
            if routine.end_date and cursor > routine.end_date:
                continue
            if cursor.isoformat() in set(routine.skip_dates):
                continue
            if cursor.weekday() not in set(routine.days_of_week):
                continue
            for block in routine.blocks or []:
                hours = _block_hours(block.start_time, block.end_time)
                focus += hours
                if (block.area or "").lower() in DEEP_WORK_AREAS:
                    deep += hours
        cursor += timedelta(days=1)

    return round(focus, 1), round(deep, 1)
