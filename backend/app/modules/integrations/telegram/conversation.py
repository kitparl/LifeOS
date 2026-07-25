"""Configuration-driven multi-step conversation engine."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.telegram.renderer import Screen
from app.modules.integrations.telegram.state import (
    clear_conversation,
    get_conversation,
    start_conversation,
    update_conversation,
)

logger = logging.getLogger(__name__)

StepHandler: TypeAlias = Callable[[AsyncSession, str, str, dict[str, Any]], Awaitable[Screen | None]]

# flow -> step -> handler
_FLOW_HANDLERS: dict[str, dict[str, StepHandler]] = {}


def register_step(flow: str, step: str):
    def decorator(fn: StepHandler) -> StepHandler:
        _FLOW_HANDLERS.setdefault(flow, {})[step] = fn
        return fn

    return decorator


async def begin(
    db: AsyncSession,
    user_id: str,
    flow: str,
    step: str,
    *,
    data: dict[str, Any] | None = None,
    message_id: int | None = None,
    chat_id: str | None = None,
) -> Screen:
    """Start a conversation and invoke the first step with empty text."""
    start_conversation(
        user_id, flow, step, data=data, message_id=message_id, chat_id=chat_id
    )
    return await handle_text(db, user_id, "") or Screen(text="Conversation started.")


async def handle_text(db: AsyncSession, user_id: str, text: str) -> Screen | None:
    """If user has an active conversation, route text to the current step handler."""
    state = get_conversation(user_id)
    if state is None:
        return None
    handlers = _FLOW_HANDLERS.get(state.flow) or {}
    handler = handlers.get(state.step)
    if handler is None:
        logger.warning("No conversation handler for %s/%s", state.flow, state.step)
        clear_conversation(user_id)
        return Screen(text="Conversation expired. Try again from /dashboard.")
    try:
        result = await handler(db, user_id, text, state.data)
        return result
    except Exception:
        logger.exception("Conversation step %s/%s failed", state.flow, state.step)
        clear_conversation(user_id)
        return Screen(text="Something went wrong. Conversation cancelled.")


async def advance(
    user_id: str,
    step: str,
    *,
    data: dict[str, Any] | None = None,
) -> None:
    update_conversation(user_id, step=step, data=data)


def cancel(user_id: str) -> Screen:
    clear_conversation(user_id)
    return Screen(text="Cancelled.")


def is_active(user_id: str) -> bool:
    return get_conversation(user_id) is not None
