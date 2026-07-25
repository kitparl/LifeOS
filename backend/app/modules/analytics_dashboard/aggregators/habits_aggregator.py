"""Habit analytics aggregations."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.analytics_dashboard.aggregators import utc_today, window_start
from app.modules.analytics_dashboard.schemas import HabitAnalytics, HabitItemAnalytics, HeatmapCell
from app.modules.habits.models import Habit
from app.modules.habits.stats import calculate_completion_rate, calculate_streak


def _longest_streak(habit: Habit) -> int:
    """Compute longest contiguous streak for daily habits; fall back to current for others."""
    if not habit.logs:
        return 0
    if habit.frequency != "daily":
        return calculate_streak(habit)
    dates = sorted({log.log_date for log in habit.logs})
    best = 1
    current = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best


async def build_habit_analytics(db: AsyncSession, user_id: str, range_days: int) -> HabitAnalytics:
    result = await db.execute(
        select(Habit)
        .where(Habit.user_id == user_id, Habit.is_active.is_(True))
        .options(selectinload(Habit.logs))
    )
    habits = list(result.scalars().all())
    items: list[HabitItemAnalytics] = []
    day_counts: dict[str, float] = defaultdict(float)
    start = window_start(range_days)

    for habit in habits:
        streak = calculate_streak(habit)
        longest = _longest_streak(habit)
        consistency = calculate_completion_rate(habit, lookback_days=range_days)
        weekly = calculate_completion_rate(habit, lookback_days=7)
        monthly = calculate_completion_rate(habit, lookback_days=30)
        items.append(
            HabitItemAnalytics(
                id=habit.id,
                name=habit.name,
                current_streak=streak,
                longest_streak=longest,
                consistency_pct=consistency,
                weekly_completion=weekly,
                monthly_completion=monthly,
            )
        )
        for log in habit.logs:
            if log.log_date >= start:
                day_counts[log.log_date.isoformat()] += 1

    today = utc_today()
    heatmap: list[HeatmapCell] = []
    cursor = start
    while cursor <= today:
        key = cursor.isoformat()
        val = day_counts.get(key, 0.0)
        heatmap.append(HeatmapCell(date=key, value=val, completed=val > 0))
        cursor += timedelta(days=1)

    best = max(items, key=lambda h: h.consistency_pct).name if items else None
    worst = min(items, key=lambda h: h.consistency_pct).name if items else None

    return HabitAnalytics(
        habits=items,
        current_streak_max=max((h.current_streak for h in items), default=0),
        longest_streak_max=max((h.longest_streak for h in items), default=0),
        consistency_avg=round(sum(h.consistency_pct for h in items) / len(items), 1) if items else 0.0,
        weekly_completion_avg=round(sum(h.weekly_completion for h in items) / len(items), 1) if items else 0.0,
        monthly_completion_avg=round(sum(h.monthly_completion for h in items) / len(items), 1) if items else 0.0,
        heatmap=heatmap,
        best_habit=best,
        worst_habit=worst,
        range_days=range_days,
    )


async def habit_consistency_avg(db: AsyncSession, user_id: str, range_days: int = 30) -> float:
    result = await db.execute(
        select(Habit)
        .where(Habit.user_id == user_id, Habit.is_active.is_(True))
        .options(selectinload(Habit.logs))
    )
    habits = list(result.scalars().all())
    if not habits:
        return 50.0
    rates = [calculate_completion_rate(h, lookback_days=range_days) for h in habits]
    return round(sum(rates) / len(rates), 1)
