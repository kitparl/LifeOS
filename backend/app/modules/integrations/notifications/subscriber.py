"""Integrations-side subscriber: EntityCreated → outbox + in-app notifications.

Registered at import time on the global event_bus. Source modules never import this.
Notification failures never raise to the emitter.
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
    TASK_ASSIGNED,
    TASK_ASSIGNMENT_ACCEPTED,
    TASK_ASSIGNMENT_CANCELLED,
    TASK_ASSIGNMENT_REJECTED,
    TASK_COMPLETED,
    TASK_CREATED,
    TASK_REASSIGNED,
    TASK_STATUS_CHANGED,
    EntityCreated,
    event_bus,
)
from app.modules.integrations.outbox_repository import OutboxRepository
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.telegram_config import parse_preferences
from app.modules.notifications.schemas import NotificationCreate
from app.modules.notifications.service import NotificationService

logger = logging.getLogger(__name__)

_TASK_EVENTS = {
    TASK_CREATED,
    TASK_ASSIGNED,
    TASK_ASSIGNMENT_ACCEPTED,
    TASK_ASSIGNMENT_REJECTED,
    TASK_ASSIGNMENT_CANCELLED,
    TASK_REASSIGNED,
    TASK_STATUS_CHANGED,
    TASK_COMPLETED,
}


def format_entity_message(event: EntityCreated) -> str:
    title = html.escape(event.title or "")
    when = html.escape(event.when) if event.when else None
    if event.event_type == TASK_CREATED:
        due = f" (due {when})" if when else ""
        return f"New task added: {title}{due}"
    if event.event_type == TASK_ASSIGNED:
        return f"Task assigned to you: {title}"
    if event.event_type == TASK_ASSIGNMENT_ACCEPTED:
        return f"Assignment accepted: {title}"
    if event.event_type == TASK_ASSIGNMENT_REJECTED:
        reason = f" — {when}" if when else ""
        return f"Assignment rejected: {title}{reason}"
    if event.event_type == TASK_ASSIGNMENT_CANCELLED:
        return f"Your assignment was removed: {title}"
    if event.event_type == TASK_REASSIGNED:
        if when == "previous":
            return f"Task assigned to another user: {title}"
        return f"Task reassigned to you: {title}"
    if event.event_type == TASK_STATUS_CHANGED:
        return f"Task status updated: {title}"
    if event.event_type == TASK_COMPLETED:
        return f"Task completed: {title}"
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


def _assignment_keyboard(entity_id: str, assignment_id: str | None) -> dict[str, Any]:
    sid = (entity_id or "")[:8]
    aid = (assignment_id or "")[:8]
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Accept", "callback_data": f"asg:accept:{sid}:{aid}"},
                {"text": "❌ Reject", "callback_data": f"asg:reject:{sid}:{aid}"},
            ],
            [
                {"text": "👁 View", "callback_data": f"task:view:{sid}"},
                {"text": "🏠 Home", "callback_data": "nav:home"},
            ],
        ]
    }


async def _create_in_app(db: AsyncSession, event: EntityCreated) -> None:
    if event.event_type not in _TASK_EVENTS or event.event_type == TASK_CREATED:
        # TASK_CREATED already notifies via Telegram for owner; skip duplicate in-app spam on create
        if event.event_type == TASK_CREATED:
            return
        if event.event_type not in _TASK_EVENTS:
            return
    try:
        plain = format_entity_message(event)
        # Strip HTML entities for in-app
        plain = (
            plain.replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
            .replace("&quot;", '"')
        )
        await NotificationService(db).create(
            event.user_id,
            NotificationCreate(
                message=plain,
                module="tasks",
                entity_id=event.entity_id,
                route=f"/tasks/{event.entity_id}" if event.entity_id else "/tasks",
            ),
        )
    except Exception:
        logger.exception("In-app notification failed for %s", event.event_type)


async def on_entity_created(db: AsyncSession, event: EntityCreated) -> None:
    await _create_in_app(db, event)

    repo = IntegrationRepository(db)
    conn = await repo.get_by_provider(event.user_id, "telegram")
    if conn is None or not conn.enabled:
        return
    prefs = parse_preferences(conn.config_json)
    # Prefer exact event match; fall back to task_created for assignment events if user has tasks enabled
    notify_keys = set(prefs.notify_on or [])
    if event.event_type not in notify_keys:
        if event.event_type in _TASK_EVENTS and TASK_CREATED in notify_keys:
            pass  # allow task-family events when task_created is enabled
        else:
            return
    text = format_entity_message(event)
    markup = None
    if event.event_type == TASK_CREATED and event.entity_id:
        markup = _task_action_keyboard(event.entity_id)
    elif event.event_type == TASK_ASSIGNED and event.entity_id:
        markup = _assignment_keyboard(event.entity_id, event.when)
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
