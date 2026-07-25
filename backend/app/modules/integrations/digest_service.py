"""Aggregate LifeOS reminders into a single notifier message.

Callers (API or scheduler) should use DigestService.send_digest(user_id)
which now delegates to the enriched morning scheduled report.
This module never imports TelegramClient — it goes through the Notifier registry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.repository import CalendarRepository
from app.modules.goals.service import GoalService
from app.modules.habits.service import HabitService
from app.modules.integrations.notifier import NotifierMessage
from app.modules.integrations.notifier_registry import build_user_notifier
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import DigestResponse
from app.modules.running.service import RunningService
from app.modules.tasks.repository import TaskRepository

logger = logging.getLogger(__name__)


@dataclass
class DigestContent:
    pending_tasks: list[str] = field(default_factory=list)
    upcoming_events: list[str] = field(default_factory=list)
    upcoming_races: list[str] = field(default_factory=list)
    habits_due: list[str] = field(default_factory=list)
    active_goals: list[str] = field(default_factory=list)

    def section_counts(self) -> dict[str, int]:
        return {
            "tasks": len(self.pending_tasks),
            "calendar": len(self.upcoming_events),
            "running": len(self.upcoming_races),
            "habits": len(self.habits_due),
            "goals": len(self.active_goals),
        }

    @property
    def is_empty(self) -> bool:
        return sum(self.section_counts().values()) == 0


def format_digest(content: DigestContent, *, now: datetime | None = None) -> NotifierMessage:
    """Pure formatter — easy to unit test without I/O."""
    from app.modules.integrations import telegram_templates as tpl

    text = tpl.digest_message(
        stamp=now or datetime.now(timezone.utc),
        pending_tasks=content.pending_tasks,
        upcoming_events=content.upcoming_events,
        upcoming_races=content.upcoming_races,
        habits_due=content.habits_due,
        active_goals=content.active_goals,
    )
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📋 Tasks", "callback_data": "task:list:0"},
                {"text": "📅 Calendar", "callback_data": "cal:today"},
            ],
            [
                {"text": "🔁 Habits", "callback_data": "habit:list"},
                {"text": "🎯 Goals", "callback_data": "goal:list"},
            ],
            [
                {"text": "🏠 Home", "callback_data": "nav:home"},
            ],
        ]
    }
    return NotifierMessage(text=text, parse_mode="HTML", reply_markup=keyboard)


class DigestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_digest(self, user_id: str) -> DigestContent:
        content = DigestContent()

        task_repo = TaskRepository(self.db)
        for status_name in ("pending", "in_progress"):
            tasks = await task_repo.list_tasks(user_id, status=status_name)
            for t in tasks:
                due = t.due_date.date().isoformat() if t.due_date else "no due date"
                content.pending_tasks.append(f"{t.title} [{status_name}, {due}]")

        events = await CalendarRepository(self.db).get_upcoming(user_id, limit=10)
        for e in events:
            when = e.starts_at.strftime("%Y-%m-%d %H:%M") if e.starts_at else "?"
            content.upcoming_events.append(f"{e.title} @ {when}")

        races = await RunningService(self.db).list_races(user_id, upcoming_only=True)
        for r in races[:10]:
            content.upcoming_races.append(f"{r.name} · {r.race_date}")

        habits = await HabitService(self.db).list_habits(user_id, active_only=True)
        for h in habits:
            if not h.completed_today:
                content.habits_due.append(f"{h.name} ({h.frequency})")

        goals = await GoalService(self.db).list_goals(user_id, status="active")
        for g in goals[:10]:
            target = g.target_date.date().isoformat() if g.target_date else "no target"
            content.active_goals.append(f"{g.title} · {g.progress}% · {target}")

        return content

    async def send_digest(self, user_id: str) -> DigestResponse:
        """Manual / scheduled entry: enriched morning report (Cycle 8)."""
        from app.modules.integrations.scheduled_report_service import ScheduledReportService

        return await ScheduledReportService(self.db).run(user_id, "morning")
