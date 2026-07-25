"""Overview KPI aggregations and Life Score."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics_dashboard.aggregators.focus_aggregator import planned_focus_hours
from app.modules.analytics_dashboard.aggregators.goals_aggregator import mean_active_progress
from app.modules.analytics_dashboard.aggregators.habits_aggregator import habit_consistency_avg
from app.modules.analytics_dashboard.aggregators.journal_aggregator import mood_score_avg, writing_streak
from app.modules.analytics_dashboard.aggregators.tasks_aggregator import (
    completed_in_range,
    completion_rate,
    todays_open_tasks,
)
from app.modules.analytics_dashboard.schemas import AnalyticsOverview, KpiCard
from app.modules.calendar.models import CalendarEvent
from app.modules.tasks.models import Task

# Life Score weights (must sum to 1.0)
LIFE_SCORE_WEIGHTS = {
    "tasks": 0.25,
    "habits": 0.25,
    "goals": 0.20,
    "journal": 0.15,
    "mood": 0.15,
}


def compute_life_score(
    task_rate: float,
    habit_rate: float,
    goal_progress: float,
    journal_streak: int,
    mood: float | None,
) -> float:
    journal_norm = min(journal_streak / 14.0, 1.0) * 100.0
    mood_norm = mood if mood is not None else 50.0
    score = (
        LIFE_SCORE_WEIGHTS["tasks"] * task_rate
        + LIFE_SCORE_WEIGHTS["habits"] * habit_rate
        + LIFE_SCORE_WEIGHTS["goals"] * goal_progress
        + LIFE_SCORE_WEIGHTS["journal"] * journal_norm
        + LIFE_SCORE_WEIGHTS["mood"] * mood_norm
    )
    return round(min(max(score, 0.0), 100.0), 1)


async def upcoming_events(db: AsyncSession, user_id: str, limit: int = 10) -> list[dict]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(CalendarEvent)
        .where(CalendarEvent.user_id == user_id, CalendarEvent.starts_at >= now)
        .order_by(CalendarEvent.starts_at.asc())
        .limit(limit)
    )
    events = list(result.scalars().all())
    return [
        {
            "id": e.id,
            "title": e.title,
            "starts_at": e.starts_at.isoformat() if e.starts_at else None,
            "category": e.category,
        }
        for e in events
    ]


async def recent_activity(db: AsyncSession, user_id: str, limit: int = 10) -> list[dict]:
    """Recent completed tasks as a lightweight activity feed."""
    result = await db.execute(
        select(Task)
        .where(
            Task.user_id == user_id,
            Task.status == "completed",
            Task.completed_at.is_not(None),
        )
        .order_by(Task.completed_at.desc())
        .limit(limit)
    )
    tasks = list(result.scalars().all())
    return [
        {
            "id": t.id,
            "title": t.title,
            "module": "tasks",
            "occurred_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in tasks
    ]


async def build_overview(db: AsyncSession, user_id: str, range_days: int) -> AnalyticsOverview:
    task_rate = await completion_rate(db, user_id, range_days)
    habit_rate = await habit_consistency_avg(db, user_id, range_days)
    goal_prog = await mean_active_progress(db, user_id)
    j_streak = await writing_streak(db, user_id)
    mood = await mood_score_avg(db, user_id, range_days)
    life = compute_life_score(task_rate, habit_rate, goal_prog, j_streak, mood)

    todays = await todays_open_tasks(db, user_id)
    completed = await completed_in_range(db, user_id, range_days)
    focus, _deep = await planned_focus_hours(db, user_id, range_days)
    upcoming = await upcoming_events(db, user_id)
    recent = await recent_activity(db, user_id)

    kpis = [
        KpiCard(id="life_score", title="Life Score", value=life, unit="/100"),
        KpiCard(id="todays_tasks", title="Today's Tasks", value=todays),
        KpiCard(id="completed_tasks", title="Completed Tasks", value=completed, subtitle=f"Last {range_days}d"),
        KpiCard(id="goal_progress", title="Goal Progress", value=goal_prog, unit="%"),
        KpiCard(id="habit_score", title="Habit Score", value=habit_rate, unit="%"),
        KpiCard(
            id="focus_time",
            title="Focus Time",
            value=focus,
            unit="h",
            subtitle="Planned from routines",
        ),
        KpiCard(id="journal_streak", title="Journal Streak", value=j_streak, unit="days"),
        KpiCard(
            id="mood",
            title="Mood",
            value=mood if mood is not None else "—",
            unit="/100" if mood is not None else None,
        ),
        KpiCard(id="upcoming_events", title="Upcoming Events", value=len(upcoming)),
        KpiCard(id="recent_activity", title="Recent Activity", value=len(recent)),
    ]

    return AnalyticsOverview(
        life_score=life,
        todays_tasks=todays,
        completed_tasks=completed,
        goal_progress=goal_prog,
        habit_score=habit_rate,
        focus_time_hours=focus,
        focus_time_label="planned",
        journal_streak=j_streak,
        mood_score=mood,
        upcoming_events=upcoming,
        recent_activity=recent,
        kpis=kpis,
        range_days=range_days,
    )
