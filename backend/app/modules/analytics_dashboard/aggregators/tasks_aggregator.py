"""Task productivity aggregations."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics_dashboard.aggregators import utc_today, window_start
from app.modules.analytics_dashboard.schemas import HeatmapCell, SeriesPoint, TimeSeries
from app.modules.tasks.models import OPEN_TASK_STATUSES, Task


def _alive():
    return Task.deleted_at.is_(None)


async def task_completion_breakdown(db: AsyncSession, user_id: str, range_days: int) -> list[SeriesPoint]:
    start = window_start(range_days)
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    rows = await db.execute(
        select(Task.status, func.count())
        .where(Task.user_id == user_id, _alive(), Task.created_at >= start_dt)
        .group_by(Task.status)
    )
    return [SeriesPoint(label=str(status), value=float(count)) for status, count in rows.all()]


async def overdue_count(db: AsyncSession, user_id: str) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(func.count())
        .select_from(Task)
        .where(
            Task.user_id == user_id,
            _alive(),
            Task.status.in_(OPEN_TASK_STATUSES),
            Task.due_date.is_not(None),
            Task.due_date < now,
        )
    )
    return int(result.scalar() or 0)


async def category_distribution(db: AsyncSession, user_id: str, range_days: int) -> list[SeriesPoint]:
    """Group by raw category; coalesce NULL → uncategorized in Python.

    Avoids Postgres GroupingError when SQLAlchemy emits coalesce() with
    different bind params in SELECT vs GROUP BY.
    """
    start = window_start(range_days)
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    rows = await db.execute(
        select(Task.category, func.count())
        .where(Task.user_id == user_id, _alive(), Task.created_at >= start_dt)
        .group_by(Task.category)
    )
    return [
        SeriesPoint(label=str(label or "uncategorized"), value=float(count))
        for label, count in rows.all()
    ]


async def completed_series(
    db: AsyncSession, user_id: str, range_days: int
) -> tuple[TimeSeries, TimeSeries, TimeSeries, list[HeatmapCell]]:
    """Daily / weekly / monthly completed-task series + completion heatmap."""
    today = utc_today()
    start = window_start(range_days, today)
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)

    rows = await db.execute(
        select(Task.completed_at)
        .where(
            Task.user_id == user_id,
            _alive(),
            Task.status == "completed",
            Task.completed_at.is_not(None),
            Task.completed_at >= start_dt,
        )
    )
    dates: list = []
    for (completed_at,) in rows.all():
        if completed_at is None:
            continue
        d = completed_at.date() if hasattr(completed_at, "date") else completed_at
        dates.append(d)

    daily_map: dict[str, float] = defaultdict(float)
    weekly_map: dict[str, float] = defaultdict(float)
    monthly_map: dict[str, float] = defaultdict(float)
    for d in dates:
        daily_map[d.isoformat()] += 1
        week_start = d - timedelta(days=d.weekday())
        weekly_map[week_start.isoformat()] += 1
        monthly_map[d.replace(day=1).isoformat()] += 1

    daily_points: list[SeriesPoint] = []
    heatmap: list[HeatmapCell] = []
    cursor = start
    while cursor <= today:
        key = cursor.isoformat()
        val = daily_map.get(key, 0.0)
        daily_points.append(SeriesPoint(label=key, value=val))
        heatmap.append(HeatmapCell(date=key, value=val, completed=val > 0))
        cursor += timedelta(days=1)

    weekly_points = [
        SeriesPoint(label=k, value=v) for k, v in sorted(weekly_map.items())
    ]
    monthly_points = [
        SeriesPoint(label=k, value=v) for k, v in sorted(monthly_map.items())
    ]

    return (
        TimeSeries(key="daily_tasks", label="Daily Tasks Completed", points=daily_points),
        TimeSeries(key="weekly_tasks", label="Weekly Tasks Completed", points=weekly_points),
        TimeSeries(key="monthly_tasks", label="Monthly Tasks Completed", points=monthly_points),
        heatmap,
    )


async def todays_open_tasks(db: AsyncSession, user_id: str) -> int:
    today = utc_today()
    start_dt = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    result = await db.execute(
        select(func.count())
        .select_from(Task)
        .where(
            Task.user_id == user_id,
            _alive(),
            Task.status.in_(OPEN_TASK_STATUSES),
            Task.due_date.is_not(None),
            Task.due_date >= start_dt,
            Task.due_date < end_dt,
        )
    )
    return int(result.scalar() or 0)


async def completed_in_range(db: AsyncSession, user_id: str, range_days: int) -> int:
    start = window_start(range_days)
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    result = await db.execute(
        select(func.count())
        .select_from(Task)
        .where(
            Task.user_id == user_id,
            _alive(),
            Task.status == "completed",
            Task.completed_at.is_not(None),
            Task.completed_at >= start_dt,
        )
    )
    return int(result.scalar() or 0)


async def completion_rate(db: AsyncSession, user_id: str, range_days: int) -> float:
    start = window_start(range_days)
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    completed = await db.execute(
        select(func.count())
        .select_from(Task)
        .where(Task.user_id == user_id, _alive(), Task.status == "completed", Task.created_at >= start_dt)
    )
    open_ = await db.execute(
        select(func.count())
        .select_from(Task)
        .where(
            Task.user_id == user_id,
            _alive(),
            Task.status.in_(OPEN_TASK_STATUSES),
            Task.created_at >= start_dt,
        )
    )
    c = int(completed.scalar() or 0)
    o = int(open_.scalar() or 0)
    total = c + o
    if total == 0:
        return 50.0
    return round(c / total * 100, 1)


async def remaining_tasks_for_goal(db: AsyncSession, user_id: str, goal_id: str) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Task)
        .where(
            Task.user_id == user_id,
            _alive(),
            Task.goal_id == goal_id,
            Task.status.in_(OPEN_TASK_STATUSES),
        )
    )
    return int(result.scalar() or 0)
