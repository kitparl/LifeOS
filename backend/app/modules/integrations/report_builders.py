"""Build self-contained HTML report bodies for scheduled Telegram jobs.

Business data comes from domain services; this module only formats.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.service import CalendarService
from app.modules.goals.service import GoalService
from app.modules.habits.service import HabitService
from app.modules.integrations import telegram_templates as tpl
from app.modules.routines.service import RoutineService
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository


@dataclass
class ReportBuildResult:
    text: str
    sections: dict[str, int] = field(default_factory=dict)
    is_empty: bool = False


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _day_bounds(d: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    start = datetime.combine(d, datetime.min.time(), tzinfo=tz)
    end = start + timedelta(days=1)
    return start, end


def _task_line(t: Task) -> str:
    due = t.due_date.strftime("%Y-%m-%d") if t.due_date else "no due"
    return f"{t.title} [{t.status}, {due}]"


async def _open_tasks(db: AsyncSession, user_id: str) -> list[Task]:
    repo = TaskRepository(db)
    out: list[Task] = []
    for status_name in ("pending", "in_progress"):
        out.extend(await repo.list_tasks(user_id, status=status_name))
    return out


def _group_pending(tasks: list[Task], today: date, tz: ZoneInfo) -> tuple[list[str], list[str], list[str]]:
    overdue: list[str] = []
    due_today: list[str] = []
    later: list[str] = []
    for t in tasks:
        due = _aware(t.due_date)
        if due is None:
            later.append(_task_line(t))
            continue
        local_due = due.astimezone(tz)
        if local_due.date() < today:
            overdue.append(_task_line(t))
        elif local_due.date() == today:
            due_today.append(_task_line(t))
        else:
            later.append(_task_line(t))
    return overdue, due_today, later


async def _calendar_lines(
    db: AsyncSession, user_id: str, start: datetime, end: datetime, *, limit: int = 40
) -> list[str]:
    events = await CalendarService(db).list_events(user_id, start=start, end=end)
    lines: list[str] = []
    for e in events[:limit]:
        when = e.starts_at.strftime("%a %m-%d %H:%M") if e.starts_at else "?"
        kind = ""
        ek = getattr(e, "event_kind", None) or ""
        if ek == "birthday":
            kind = " 🎂"
        elif ek == "immutable":
            kind = " 🔒"
        lines.append(f"{e.title}{kind} @ {when}")
    return lines


async def _habits_open_lines(db: AsyncSession, user_id: str) -> list[str]:
    habits = await HabitService(db).list_habits(user_id, active_only=True)
    lines: list[str] = []
    for h in habits:
        if h.completed_today:
            continue
        streak_n = getattr(h, "streak", 0) or 0
        extra = f" · streak {streak_n}" if streak_n else ""
        lines.append(f"{h.name} ({h.frequency}){extra}")
    return lines


async def _goals_lines(db: AsyncSession, user_id: str, *, limit: int = 8) -> list[str]:
    goals = await GoalService(db).list_goals(user_id, status="active")
    lines: list[str] = []
    for g in goals[:limit]:
        lines.append(f"{g.title} · {g.progress}%")
    return lines


async def _routine_lines(db: AsyncSession, user_id: str, *, limit: int = 12) -> list[str]:
    preview = await RoutineService(db).today_preview(user_id, limit=limit)
    lines: list[str] = []
    for _eid, title, starts_at, _rid in preview:
        when = starts_at.strftime("%H:%M") if starts_at else "?"
        lines.append(f"{when} {title}")
    return lines


async def _linked_habit_lines_for_today(db: AsyncSession, user_id: str) -> list[str]:
    """Habits attached to today's routine blocks (best-effort; empty if no links)."""
    try:
        from app.modules.routines.models import Routine, RoutineBlock
        from sqlalchemy.orm import selectinload

        routines = await RoutineService(db).repo.list_routines(user_id, active_only=True)
        if not routines:
            return []
        tz = ZoneInfo(routines[0].timezone or "Asia/Kolkata")
        today = datetime.now(tz).date()
        weekday = today.weekday()
        lines: list[str] = []
        for r in routines:
            if weekday not in r.days_of_week:
                continue
            if today.isoformat() in r.skip_dates:
                continue
            if r.start_date and today < r.start_date:
                continue
            if r.end_date and today > r.end_date:
                continue
            for block in r.blocks:
                habits = getattr(block, "habits", None) or []
                for h in habits:
                    lines.append(f"{block.title}: {h.name}")
        return lines
    except Exception:
        return []


async def build_morning(db: AsyncSession, user_id: str, tz: ZoneInfo) -> ReportBuildResult:
    today = datetime.now(tz).date()
    start, _ = _day_bounds(today, tz)
    end = start + timedelta(days=8)

    overdue, due_today, later = _group_pending(await _open_tasks(db, user_id), today, tz)
    routine = await _routine_lines(db, user_id)
    calendar = await _calendar_lines(db, user_id, start, end)
    habits = await _habits_open_lines(db, user_id)
    linked = await _linked_habit_lines_for_today(db, user_id)
    goals = await _goals_lines(db, user_id)

    text = tpl.morning_report(
        stamp=datetime.now(tz),
        routine=routine,
        overdue=overdue,
        due_today=due_today,
        later=later,
        calendar=calendar,
        habits=habits,
        linked_habits=linked,
        goals=goals,
    )
    sections = {
        "routine": len(routine),
        "overdue": len(overdue),
        "due_today": len(due_today),
        "later": len(later),
        "calendar": len(calendar),
        "habits": len(habits),
        "goals": len(goals),
    }
    return ReportBuildResult(text=text, sections=sections, is_empty=sum(sections.values()) == 0)


async def build_midday(db: AsyncSession, user_id: str, tz: ZoneInfo) -> ReportBuildResult:
    today = datetime.now(tz).date()
    overdue, due_today, _ = _group_pending(await _open_tasks(db, user_id), today, tz)
    text = tpl.midday_nudge(
        stamp=datetime.now(tz),
        overdue=overdue,
        due_today=due_today,
    )
    sections = {"overdue": len(overdue), "due_today": len(due_today)}
    return ReportBuildResult(text=text, sections=sections, is_empty=sum(sections.values()) == 0)


async def build_night(db: AsyncSession, user_id: str, tz: ZoneInfo) -> ReportBuildResult:
    today = datetime.now(tz).date()
    day_start, day_end = _day_bounds(today, tz)
    tomorrow = today + timedelta(days=1)
    t_start, t_end = _day_bounds(tomorrow, tz)

    # Completed today
    result = await db.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.status == "completed",
            Task.completed_at.is_not(None),
            Task.completed_at >= day_start.astimezone(timezone.utc),
            Task.completed_at < day_end.astimezone(timezone.utc),
        )
    )
    completed = list(result.scalars().all())
    completed_lines = [t.title for t in completed[:15]]

    habits = await _habits_open_lines(db, user_id)
    linked = await _linked_habit_lines_for_today(db, user_id)

    # Tomorrow preview
    open_tasks = await _open_tasks(db, user_id)
    due_tomorrow = []
    for t in open_tasks:
        due = _aware(t.due_date)
        if due and due.astimezone(tz).date() == tomorrow:
            due_tomorrow.append(_task_line(t))

    # Routine for tomorrow via expand
    from app.modules.routines.service import RoutineService as RS

    t_items = await RS(db).expand_for_calendar(user_id, t_start, t_end)
    routine_tmr = [f"{i.starts_at.strftime('%H:%M')} {i.title}" for i in sorted(t_items, key=lambda x: x.starts_at)[:12]]
    calendar_tmr = await _calendar_lines(db, user_id, t_start, t_end, limit=20)

    text = tpl.night_wrap(
        stamp=datetime.now(tz),
        completed=completed_lines,
        completed_count=len(completed),
        habits=habits,
        linked_habits=linked,
        routine_tomorrow=routine_tmr,
        calendar_tomorrow=calendar_tmr,
        tasks_tomorrow=due_tomorrow,
    )
    sections = {
        "completed": len(completed),
        "habits": len(habits),
        "routine_tomorrow": len(routine_tmr),
        "calendar_tomorrow": len(calendar_tmr),
        "tasks_tomorrow": len(due_tomorrow),
    }
    return ReportBuildResult(text=text, sections=sections, is_empty=False)


async def build_weekly(db: AsyncSession, user_id: str, tz: ZoneInfo) -> ReportBuildResult:
    today = datetime.now(tz).date()
    start, _ = _day_bounds(today, tz)
    end = start + timedelta(days=8)

    goals = await _goals_lines(db, user_id, limit=15)
    habits = await HabitService(db).list_habits(user_id, active_only=True)
    streak_lines: list[str] = []
    for h in habits:
        n = getattr(h, "streak", 0) or 0
        if n > 0:
            streak_lines.append(f"{h.name} · streak {n}")
    streak_lines = sorted(streak_lines, key=lambda s: -int(s.rsplit(" ", 1)[-1]))[:15]

    calendar = await _calendar_lines(db, user_id, start, end, limit=40)
    text = tpl.weekly_review(
        stamp=datetime.now(tz),
        goals=goals,
        streaks=streak_lines,
        calendar=calendar,
    )
    sections = {"goals": len(goals), "streaks": len(streak_lines), "calendar": len(calendar)}
    return ReportBuildResult(text=text, sections=sections, is_empty=False)


async def build_ai_briefing(db: AsyncSession, user_id: str, tz: ZoneInfo) -> ReportBuildResult:
    from app.modules.reports.service import ReportsService

    try:
        review = await ReportsService(db).generate_review(user_id, "daily")
        content = (review.content or "").strip()
    except Exception as exc:
        return ReportBuildResult(
            text=tpl.join_blocks(tpl._header("AI Daily Briefing"), f"Unavailable: {tpl.esc(str(exc)[:200])}"),
            sections={"ai": 0},
            is_empty=True,
        )
    if not content:
        return ReportBuildResult(text="", sections={"ai": 0}, is_empty=True)
    text = tpl.join_blocks(
        tpl._header("AI Daily Briefing", datetime.now(tz).strftime("%Y-%m-%d %H:%M")),
        tpl.esc(content[:3500]),
    )
    return ReportBuildResult(text=text, sections={"ai": 1}, is_empty=False)


BUILDERS = {
    "morning": build_morning,
    "midday": build_midday,
    "night": build_night,
    "weekly": build_weekly,
    "ai_briefing": build_ai_briefing,
}

# Jobs that skip send when content is empty
SKIP_IF_EMPTY = frozenset({"midday", "ai_briefing"})
