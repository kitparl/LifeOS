"""Lightweight in-process domain event bus.

Source modules emit events; integrations (and future subscribers) handle them.
Handlers must never raise to the emitter — emit() swallows handler errors.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Event type constants (also used as notify_on preference keys)
TASK_CREATED = "task_created"
TASK_ASSIGNED = "task_assigned"
TASK_ASSIGNMENT_ACCEPTED = "task_assignment_accepted"
TASK_ASSIGNMENT_REJECTED = "task_assignment_rejected"
TASK_ASSIGNMENT_CANCELLED = "task_assignment_cancelled"
TASK_REASSIGNED = "task_reassigned"
TASK_STATUS_CHANGED = "task_status_changed"
TASK_COMPLETED = "task_completed"
RACE_ADDED = "race_added"
CALENDAR_EVENT_CREATED = "calendar_event_created"
HABIT_CREATED = "habit_created"
GOAL_CREATED = "goal_created"
GOAL_MILESTONE_ADDED = "goal_milestone_added"

ALL_EVENT_TYPES: tuple[str, ...] = (
    TASK_CREATED,
    TASK_ASSIGNED,
    TASK_ASSIGNMENT_ACCEPTED,
    TASK_ASSIGNMENT_REJECTED,
    TASK_ASSIGNMENT_CANCELLED,
    TASK_REASSIGNED,
    TASK_STATUS_CHANGED,
    TASK_COMPLETED,
    RACE_ADDED,
    CALENDAR_EVENT_CREATED,
    HABIT_CREATED,
    GOAL_CREATED,
    GOAL_MILESTONE_ADDED,
)

DEFAULT_NOTIFY_ON: list[str] = list(ALL_EVENT_TYPES)


@dataclass(frozen=True)
class EntityCreated:
    """Snapshot of a newly created entity for notification formatting."""

    event_type: str
    user_id: str
    entity_id: str
    title: str
    when: str | None = None
    module: str = ""


EventHandler = Callable[[AsyncSession, EntityCreated], Awaitable[Any]]


class EventBus:
    """Minimal async pub/sub. Handlers run sequentially in the caller's session."""

    def __init__(self) -> None:
        self._handlers: list[EventHandler] = []

    def subscribe(self, handler: EventHandler) -> None:
        if handler not in self._handlers:
            self._handlers.append(handler)

    async def emit(self, db: AsyncSession, event: EntityCreated) -> None:
        for handler in self._handlers:
            try:
                await handler(db, event)
            except Exception:
                logger.exception(
                    "Event handler failed for %s (user=%s); continuing",
                    event.event_type,
                    event.user_id,
                )


event_bus = EventBus()
