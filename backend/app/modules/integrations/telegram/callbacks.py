"""Callback data parsing and dispatch registry."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CallbackContext:
    db: AsyncSession
    user_id: str
    chat_id: str
    message_id: int | None
    callback_id: str
    data: str
    namespace: str
    action: str
    args: tuple[str, ...]


CallbackHandler: TypeAlias = Callable[[CallbackContext], Awaitable[Any]]

_HANDLERS: dict[str, CallbackHandler] = {}


def register(namespace: str, action: str | None = None):
    """Decorator: register a handler for `namespace` or `namespace:action`."""

    def decorator(fn: CallbackHandler) -> CallbackHandler:
        key = f"{namespace}:{action}" if action else namespace
        _HANDLERS[key] = fn
        return fn

    return decorator


def parse_callback(data: str) -> tuple[str, str, tuple[str, ...]]:
    """Split `ns:action:arg1:arg2` → (ns, action, args)."""
    parts = (data or "").split(":")
    if len(parts) < 2:
        return parts[0] if parts else "", "", ()
    return parts[0], parts[1], tuple(parts[2:])


async def dispatch(ctx: CallbackContext) -> Any:
    """Route to the most specific registered handler."""
    specific = f"{ctx.namespace}:{ctx.action}"
    handler = _HANDLERS.get(specific) or _HANDLERS.get(ctx.namespace)
    if handler is None:
        logger.warning("No callback handler for %s", ctx.data)
        from app.modules.integrations.telegram.renderer import Screen

        return Screen(text="Unknown action. Try /dashboard.", keyboard=None)
    return await handler(ctx)


def clear_handlers_for_tests() -> None:
    """Not used in production — reserved if tests need isolation."""
    pass


def list_handlers() -> list[str]:
    return sorted(_HANDLERS.keys())
