"""In-memory conversation / opaque-token state with TTL."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationState:
    user_id: str
    flow: str
    step: str
    data: dict[str, Any] = field(default_factory=dict)
    message_id: int | None = None
    chat_id: str | None = None
    expires_at: float = 0.0


# user_id -> ConversationState
_conversations: dict[str, ConversationState] = {}
# opaque token -> payload dict (for long callback params)
_tokens: dict[str, tuple[float, dict[str, Any]]] = {}

DEFAULT_TTL_SECONDS = 15 * 60


def _now() -> float:
    return time.time()


def _purge() -> None:
    now = _now()
    expired = [k for k, v in _conversations.items() if v.expires_at <= now]
    for k in expired:
        _conversations.pop(k, None)
    expired_t = [k for k, (exp, _) in _tokens.items() if exp <= now]
    for k in expired_t:
        _tokens.pop(k, None)


def start_conversation(
    user_id: str,
    flow: str,
    step: str,
    *,
    data: dict[str, Any] | None = None,
    message_id: int | None = None,
    chat_id: str | None = None,
    ttl: int = DEFAULT_TTL_SECONDS,
) -> ConversationState:
    _purge()
    state = ConversationState(
        user_id=user_id,
        flow=flow,
        step=step,
        data=dict(data or {}),
        message_id=message_id,
        chat_id=chat_id,
        expires_at=_now() + ttl,
    )
    _conversations[user_id] = state
    return state


def get_conversation(user_id: str) -> ConversationState | None:
    _purge()
    state = _conversations.get(user_id)
    if state is None:
        return None
    if state.expires_at <= _now():
        _conversations.pop(user_id, None)
        return None
    return state


def update_conversation(
    user_id: str,
    *,
    step: str | None = None,
    data: dict[str, Any] | None = None,
    message_id: int | None = None,
    ttl: int = DEFAULT_TTL_SECONDS,
) -> ConversationState | None:
    state = get_conversation(user_id)
    if state is None:
        return None
    if step is not None:
        state.step = step
    if data is not None:
        state.data.update(data)
    if message_id is not None:
        state.message_id = message_id
    state.expires_at = _now() + ttl
    return state


def clear_conversation(user_id: str) -> None:
    _conversations.pop(user_id, None)


def put_token(payload: dict[str, Any], *, ttl: int = DEFAULT_TTL_SECONDS) -> str:
    """Store a payload under a short opaque token (fits in callback_data)."""
    _purge()
    token = secrets.token_urlsafe(6)[:8]
    _tokens[token] = (_now() + ttl, dict(payload))
    return token


def get_token(token: str) -> dict[str, Any] | None:
    _purge()
    entry = _tokens.get(token)
    if entry is None:
        return None
    exp, payload = entry
    if exp <= _now():
        _tokens.pop(token, None)
        return None
    return dict(payload)


def clear_all_for_tests() -> None:
    """Test helper — wipe all in-memory state."""
    _conversations.clear()
    _tokens.clear()
