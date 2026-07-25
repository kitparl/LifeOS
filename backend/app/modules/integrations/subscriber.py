"""Integrations-side subscriber: EntityCreated → outbox row (same transaction).

Registered at import time on the global event_bus. Source modules never import this.
"""

from __future__ import annotations

import html
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import (
    CALENDAR_EVENT_CREATED,
    GOAL_CREATED,
    GOAL_MILESTONE_ADDED,
    HABIT_CREATED,
    RACE_ADDED,
    TASK_CREATED,
    EntityCreated,
    event_bus,
)
from app.modules.integrations.outbox_repository import OutboxRepository
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.telegram_config import parse_preferences

logger = logging.getLogger(__name__)


def format_entity_message(event: EntityCreated) -> str:
    title = html.escape(event.title or "")
    when = html.escape(event.when) if event.when else None
    if event.event_type == TASK_CREATED:
        due = f" (due {when})" if when else ""
        return f"New task added: {title}{due}"
    if event.event_type == RACE_ADDED:
        on = f" on {when}" if when else ""
        return f"New race added: {title}{on}"
    if event.event_type == CALENDAR_EVENT_CREATED:
        on = f" at {when}" if when else ""
        return f"New calendar event: {title}{on}"
    if event.event_type == HABIT_CREATED:
        freq = f" ({when})" if when else ""
        return f"New habit created: {title}{freq}"
    if event.event_type == GOAL_CREATED:
        target = f" (target {when})" if when else ""
        return f"New goal created: {title}{target}"
    if event.event_type == GOAL_MILESTONE_ADDED:
        return f"Goal milestone added: {title}"
    return f"LifeOS update: {title}"


def _task_action_keyboard(entity_id: str) -> dict[str, Any]:
    sid = (entity_id or "")[:8]
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Mark done", "callback_data": f"task:done:{sid}"},
                {"text": "👁 View", "callback_data": f"task:view:{sid}"},
            ],
            [
                {"text": "📋 Tasks", "callback_data": "task:list:0"},
                {"text": "🏠 Home", "callback_data": "nav:home"},
            ],
        ]
    }


async def on_entity_created(db: AsyncSession, event: EntityCreated) -> None:
    repo = IntegrationRepository(db)
    conn = await repo.get_by_provider(event.user_id, "telegram")
    if conn is None or not conn.enabled:
        return
    prefs = parse_preferences(conn.config_json)
    if event.event_type not in prefs.notify_on:
        return
    text = format_entity_message(event)
    markup = None
    if event.event_type == TASK_CREATED and event.entity_id:
        markup = _task_action_keyboard(event.entity_id)
    await OutboxRepository(db).enqueue(
        event.user_id,
        text,
        channel="telegram",
        parse_mode="HTML",
        reply_markup=markup,
    )
    try:
        db.info["outbox_enqueued"] = True
    except Exception:
        pass


def register_subscribers() -> None:
    """Idempotent registration — safe to call from lifespan."""
    event_bus.subscribe(on_entity_created)


# Auto-register on import so any emit after import is handled.
register_subscribers()
