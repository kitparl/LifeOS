"""Inbound Telegram command registry.

Additive: add a new entry to COMMANDS to support another bot command.
Handlers receive (db, user_id, args) and return reply text.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from datetime import date, datetime, time, timezone
from typing import TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

CommandHandlerFn: TypeAlias = Callable[[AsyncSession, str, str], Awaitable[str]]


async def cmd_help(db: AsyncSession, user_id: str, args: str) -> str:
    return (
        "LifeOS bot commands:\n"
        "/tasks — pending tasks\n"
        "/today — today's agenda\n"
        "/done <id> — complete a task\n"
        "/habits — habits due\n"
        "/goals — active goals\n"
        "/help — this message"
    )


async def cmd_tasks(db: AsyncSession, user_id: str, args: str) -> str:
    from app.modules.tasks.service import TaskService

    items = await TaskService(db).list_tasks(user_id, status="pending")
    in_prog = await TaskService(db).list_tasks(user_id, status="in_progress")
    all_items = list(items) + list(in_prog)
    if not all_items:
        return "No pending tasks. Nice work!"
    lines = ["Pending tasks:"]
    for t in all_items[:20]:
        due = t.due_date.date().isoformat() if t.due_date else "no due"
        lines.append(f"• [{t.id[:8]}] {t.title} ({t.status}, {due})")
    if len(all_items) > 20:
        lines.append(f"…and {len(all_items) - 20} more")
    return "\n".join(lines)


async def cmd_today(db: AsyncSession, user_id: str, args: str) -> str:
    from app.modules.calendar.repository import CalendarRepository
    from app.modules.running.service import RunningService
    from app.modules.tasks.service import TaskService

    today = date.today()
    start = datetime.combine(today, time.min, tzinfo=timezone.utc)
    end = datetime.combine(today, time.max, tzinfo=timezone.utc)

    lines = [f"Today ({today.isoformat()}):", ""]

    due_tasks = await TaskService(db).list_tasks(user_id, due_today=True)
    if due_tasks:
        lines.append("Tasks due today:")
        for t in due_tasks[:10]:
            lines.append(f"• [{t.id[:8]}] {t.title}")
        lines.append("")

    events = await CalendarRepository(db).list_events(user_id, start=start, end=end)
    if events:
        lines.append("Calendar:")
        for e in events[:10]:
            when = e.starts_at.strftime("%H:%M") if e.starts_at else "?"
            lines.append(f"• {when} {e.title}")
        lines.append("")

    races = await RunningService(db).list_races(user_id, upcoming_only=True)
    today_races = [r for r in races if str(r.race_date) == today.isoformat()]
    if today_races:
        lines.append("Races:")
        for r in today_races:
            lines.append(f"• {r.name}")
        lines.append("")

    if len(lines) <= 2:
        lines.append("Nothing scheduled for today.")
    return "\n".join(lines).strip()


async def cmd_done(db: AsyncSession, user_id: str, args: str) -> str:
    from app.modules.tasks.repository import TaskRepository
    from app.modules.tasks.service import TaskService

    token = (args or "").strip().split()[0] if args.strip() else ""
    if not token:
        return "Usage: /done <task_id_prefix>"

    repo = TaskRepository(db)
    # Match by full id or prefix
    tasks = await repo.list_tasks(user_id, status="pending")
    tasks += await repo.list_tasks(user_id, status="in_progress")
    matches = [t for t in tasks if t.id.startswith(token) or t.id == token]
    if not matches:
        return f"No open task matching '{token}'."
    if len(matches) > 1:
        lines = ["Ambiguous id — matches:"]
        for t in matches[:5]:
            lines.append(f"• [{t.id[:8]}] {t.title}")
        return "\n".join(lines)

    await TaskService(db).complete_task(user_id, matches[0].id)
    return f"Done: {matches[0].title}"


async def cmd_habits(db: AsyncSession, user_id: str, args: str) -> str:
    from app.modules.habits.service import HabitService

    habits = await HabitService(db).list_habits(user_id, active_only=True)
    due = [h for h in habits if not h.completed_today]
    if not due:
        return "All active habits completed for this period."
    lines = ["Habits due:"]
    for h in due[:20]:
        lines.append(f"• {h.name} ({h.frequency})")
    return "\n".join(lines)


async def cmd_goals(db: AsyncSession, user_id: str, args: str) -> str:
    from app.modules.goals.service import GoalService

    goals = await GoalService(db).list_goals(user_id, status="active")
    if not goals:
        return "No active goals."
    lines = ["Active goals:"]
    for g in goals[:15]:
        target = g.target_date.date().isoformat() if g.target_date else "no target"
        lines.append(f"• {g.title} · {g.progress}% · {target}")
    return "\n".join(lines)


COMMANDS: dict[str, CommandHandlerFn] = {
    "/help": cmd_help,
    "/start": cmd_help,
    "/tasks": cmd_tasks,
    "/today": cmd_today,
    "/done": cmd_done,
    "/habits": cmd_habits,
    "/goals": cmd_goals,
}

_CMD_RE = re.compile(r"^(/[a-zA-Z_]+)(?:@[^\s]+)?(?:\s+(.*))?$", re.DOTALL)


async def handle_command(db: AsyncSession, user_id: str, text: str) -> str:
    """Parse and dispatch a command. Unknown commands get a short help hint."""
    raw = (text or "").strip()
    if not raw.startswith("/"):
        return "Send a command like /help to get started."
    m = _CMD_RE.match(raw)
    if not m:
        return "Unrecognized command. Try /help."
    cmd = m.group(1).lower()
    args = (m.group(2) or "").strip()
    handler = COMMANDS.get(cmd)
    if handler is None:
        return f"Unknown command {cmd}. Try /help."
    try:
        return await handler(db, user_id, args)
    except Exception:
        logger.exception("Command %s failed for user=%s", cmd, user_id)
        return "Sorry, something went wrong running that command."
