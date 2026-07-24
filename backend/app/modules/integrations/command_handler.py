"""Inbound Telegram command registry.

Additive: add a new entry to COMMANDS to support another bot command.
Handlers receive (db, user_id, args) and return reply text (HTML templates).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from datetime import date, datetime, time, timedelta, timezone
from typing import TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations import telegram_templates as tpl

logger = logging.getLogger(__name__)

CommandHandlerFn: TypeAlias = Callable[[AsyncSession, str, str], Awaitable[str]]


async def cmd_help(db: AsyncSession, user_id: str, args: str) -> str:
    return tpl.help_message()


async def cmd_tasks(db: AsyncSession, user_id: str, args: str) -> str:
    from app.modules.tasks.service import TaskService

    items = await TaskService(db).list_tasks(user_id, status="pending")
    in_prog = await TaskService(db).list_tasks(user_id, status="in_progress")
    all_items = list(items) + list(in_prog)
    if not all_items:
        return tpl.tasks_empty()
    lines = [
        tpl.task_line(
            short_id=t.id[:8],
            title=t.title,
            status=t.status,
            due=t.due_date.date().isoformat() if t.due_date else "no due",
        )
        for t in all_items
    ]
    return tpl.tasks_list(lines, total=len(all_items))


async def cmd_today(db: AsyncSession, user_id: str, args: str) -> str:
    from app.modules.calendar.repository import CalendarRepository
    from app.modules.running.service import RunningService
    from app.modules.tasks.service import TaskService

    today = date.today()
    start = datetime.combine(today, time.min, tzinfo=timezone.utc)
    end = datetime.combine(today, time.max, tzinfo=timezone.utc)

    due_tasks = await TaskService(db).list_tasks(user_id, due_today=True)
    task_lines = [f"[{t.id[:8]}] {t.title}" for t in due_tasks[:10]]

    events = await CalendarRepository(db).list_events(user_id, start=start, end=end)
    cal_lines = [
        f"{e.starts_at.strftime('%H:%M') if e.starts_at else '?'} {e.title}"
        for e in events[:10]
    ]

    races = await RunningService(db).list_races(user_id, upcoming_only=True)
    race_lines = [r.name for r in races if str(r.race_date) == today.isoformat()]

    return tpl.today_agenda(today, tasks=task_lines, calendar=cal_lines, races=race_lines)


async def cmd_done(db: AsyncSession, user_id: str, args: str) -> str:
    from app.modules.tasks.repository import TaskRepository
    from app.modules.tasks.service import TaskService

    token = (args or "").strip().split()[0] if args.strip() else ""
    if not token:
        return tpl.done_usage()

    repo = TaskRepository(db)
    tasks = await repo.list_tasks(user_id, status="pending")
    tasks += await repo.list_tasks(user_id, status="in_progress")
    matches = [t for t in tasks if t.id.startswith(token) or t.id == token]
    if not matches:
        return tpl.done_not_found(token)
    if len(matches) > 1:
        lines = [f"[{t.id[:8]}] {t.title}" for t in matches[:5]]
        return tpl.done_ambiguous(lines)

    await TaskService(db).complete_task(user_id, matches[0].id)
    return tpl.done_success(matches[0].title)


async def cmd_add_task(db: AsyncSession, user_id: str, args: str) -> str:
    from app.modules.tasks.schemas import TaskCreate
    from app.modules.tasks.service import TaskService

    raw = (args or "").strip()
    if not raw:
        return tpl.add_task_usage()

    title, due_dt, due_error = _parse_add_task_args(raw)
    if due_error:
        return tpl.add_task_bad_due(due_error)
    if not title:
        return tpl.add_task_usage()
    if len(title) > 200:
        return tpl.add_task_too_long()

    task = await TaskService(db).create_task(
        user_id, TaskCreate(title=title, due_date=due_dt)
    )
    due_label = task.due_date.date().isoformat() if task.due_date else "today"
    return tpl.add_task_success(short_id=task.id[:8], title=task.title, due=due_label)


def _parse_add_task_args(raw: str) -> tuple[str, datetime, str | None]:
    """Split title and optional due date. Default due = today (UTC end-friendly noon).

    Supported endings:
      ... due 2026-08-01
      ... 2026-08-01
      ... due today | tomorrow
      ... today | tomorrow
    """
    text = raw.strip()
    today = date.today()

    def as_due(d: date) -> datetime:
        return datetime.combine(d, time(12, 0), tzinfo=timezone.utc)

    # due YYYY-MM-DD | due today | due tomorrow
    m = re.search(
        r"\s+due\s+(today|tomorrow|\d{4}-\d{2}-\d{2})\s*$",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        token = m.group(1).lower()
        title = text[: m.start()].strip()
        parsed = _resolve_due_token(token, today)
        if parsed is None:
            return title, as_due(today), token
        return title, as_due(parsed), None

    # trailing YYYY-MM-DD | today | tomorrow (without "due")
    m = re.search(r"\s+(today|tomorrow|\d{4}-\d{2}-\d{2})\s*$", text, flags=re.IGNORECASE)
    if m:
        token = m.group(1).lower()
        # Only treat as due if it's a date keyword / ISO date (not part of a normal title word)
        title = text[: m.start()].strip()
        if title:
            parsed = _resolve_due_token(token, today)
            if parsed is None:
                return title, as_due(today), token
            return title, as_due(parsed), None

    return text, as_due(today), None


def _resolve_due_token(token: str, today: date) -> date | None:
    if token == "today":
        return today
    if token == "tomorrow":
        return today + timedelta(days=1)
    try:
        return date.fromisoformat(token)
    except ValueError:
        return None


async def cmd_habits(db: AsyncSession, user_id: str, args: str) -> str:
    from app.modules.habits.service import HabitService

    habits = await HabitService(db).list_habits(user_id, active_only=True)
    due = [h for h in habits if not h.completed_today]
    if not due:
        return tpl.habits_empty()
    lines = [f"{h.name} ({h.frequency})" for h in due]
    return tpl.habits_list(lines)


async def cmd_goals(db: AsyncSession, user_id: str, args: str) -> str:
    from app.modules.goals.service import GoalService

    goals = await GoalService(db).list_goals(user_id, status="active")
    if not goals:
        return tpl.goals_empty()
    lines = [
        f"{g.title} · {g.progress}% · "
        f"{g.target_date.date().isoformat() if g.target_date else 'no target'}"
        for g in goals
    ]
    return tpl.goals_list(lines)


COMMANDS: dict[str, CommandHandlerFn] = {
    "/help": cmd_help,
    "/start": cmd_help,
    "/add-task": cmd_add_task,
    "/tasks": cmd_tasks,
    "/today": cmd_today,
    "/done": cmd_done,
    "/habits": cmd_habits,
    "/goals": cmd_goals,
}

# Allow hyphens in command names (e.g. /add-task)
_CMD_RE = re.compile(r"^(/[a-zA-Z0-9_-]+)(?:@[^\s]+)?(?:\s+(.*))?$", re.DOTALL)


async def handle_command(db: AsyncSession, user_id: str, text: str) -> str:
    """Parse and dispatch a command. Unknown commands get a short help hint."""
    raw = (text or "").strip()
    if not raw.startswith("/"):
        return tpl.hint_send_command()
    m = _CMD_RE.match(raw)
    if not m:
        return tpl.unrecognized_command()
    cmd = m.group(1).lower()
    args = (m.group(2) or "").strip()
    handler = COMMANDS.get(cmd)
    if handler is None:
        return tpl.unknown_command(cmd)
    try:
        return await handler(db, user_id, args)
    except Exception:
        logger.exception("Command %s failed for user=%s", cmd, user_id)
        return tpl.command_error()
