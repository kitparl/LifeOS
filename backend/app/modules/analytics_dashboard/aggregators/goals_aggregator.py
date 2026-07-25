"""Goal analytics aggregations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.analytics_dashboard.aggregators import utc_today, window_start
from app.modules.analytics_dashboard.aggregators.tasks_aggregator import remaining_tasks_for_goal
from app.modules.analytics_dashboard.schemas import (
    GoalAnalytics,
    GoalItemAnalytics,
    PlaceholderField,
    SeriesPoint,
)
from app.modules.goals.models import Goal


async def mean_active_progress(db: AsyncSession, user_id: str) -> float:
    result = await db.execute(
        select(Goal.progress).where(Goal.user_id == user_id, Goal.status == "active")
    )
    values = [int(p) for (p,) in result.all()]
    if not values:
        return 50.0
    return round(sum(values) / len(values), 1)


def _velocity(goal: Goal, range_days: int) -> float:
    """Progress points per week approximated from current progress and age."""
    created = goal.created_at
    if created is None:
        return 0.0
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age_days = max((datetime.now(timezone.utc) - created).days, 1)
    weeks = max(age_days / 7.0, 1 / 7)
    return round(float(goal.progress or 0) / weeks, 2)


def _burndown(goal: Goal, range_days: int) -> list[SeriesPoint]:
    """Synthetic burndown from created→now assuming linear progress to current %."""
    today = utc_today()
    start = window_start(min(range_days, 60), today)
    created = goal.created_at.date() if goal.created_at else start
    if created > start:
        start = created
    total_days = max((today - start).days, 1)
    progress = float(goal.progress or 0)
    points: list[SeriesPoint] = []
    cursor = start
    step = max(total_days // 10, 1)
    day_i = 0
    while cursor <= today:
        frac = day_i / total_days
        remaining = 100.0 - progress * frac
        points.append(SeriesPoint(label=cursor.isoformat(), value=round(max(remaining, 100 - progress), 1)))
        cursor += timedelta(days=step)
        day_i += step
    points.append(SeriesPoint(label=today.isoformat(), value=round(100.0 - progress, 1)))
    return points


async def build_goal_analytics(db: AsyncSession, user_id: str, range_days: int) -> GoalAnalytics:
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == user_id, Goal.status.in_(("active", "completed")))
        .options(selectinload(Goal.milestones))
        .order_by(Goal.updated_at.desc())
    )
    goals = list(result.scalars().all())
    items: list[GoalItemAnalytics] = []
    velocities: list[float] = []
    progresses: list[float] = []

    for goal in goals:
        remaining = await remaining_tasks_for_goal(db, user_id, goal.id)
        milestones = list(goal.milestones or [])
        done = sum(1 for m in milestones if m.completed)
        vel = _velocity(goal, range_days)
        velocities.append(vel)
        progresses.append(float(goal.progress or 0))
        items.append(
            GoalItemAnalytics(
                id=goal.id,
                title=goal.title,
                progress=int(goal.progress or 0),
                status=goal.status,
                remaining_tasks=remaining,
                milestones_total=len(milestones),
                milestones_done=done,
                velocity=vel,
                burndown=_burndown(goal, range_days),
                completion_forecast=PlaceholderField(
                    status="coming_soon", message="Completion forecast coming soon"
                ),
                risk_indicator=PlaceholderField(
                    status="coming_soon", message="Risk indicator coming soon"
                ),
            )
        )

    return GoalAnalytics(
        goals=items,
        avg_progress=round(sum(progresses) / len(progresses), 1) if progresses else 0.0,
        avg_velocity=round(sum(velocities) / len(velocities), 2) if velocities else 0.0,
        range_days=range_days,
    )
