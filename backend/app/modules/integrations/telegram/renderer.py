"""Screen dataclass and send/edit rendering via Notifier / TelegramClient."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.notifier import NotifierMessage
from app.modules.integrations.notifier_registry import build_user_notifier
from app.modules.integrations.telegram_client import TelegramClient, TelegramClientError
from app.modules.integrations.telegram_config import parse_config
from app.modules.integrations.repository import IntegrationRepository

logger = logging.getLogger(__name__)


@dataclass
class Screen:
    text: str
    keyboard: dict[str, Any] | None = None
    parse_mode: str = "HTML"
    # If True and message_id present, edit instead of send
    edit: bool = True


async def _client_for_user(db: AsyncSession, user_id: str) -> tuple[TelegramClient, str] | None:
    repo = IntegrationRepository(db)
    conn = await repo.get_by_provider(user_id, "telegram")
    if conn is None or not conn.enabled:
        return None
    cfg = parse_config(conn.config_json)
    if cfg is None:
        return None
    return TelegramClient(cfg.bot_token), cfg.chat_id


async def render_screen(
    db: AsyncSession,
    user_id: str,
    screen: Screen,
    *,
    message_id: int | None = None,
    callback_id: str | None = None,
    callback_toast: str | None = None,
) -> dict[str, Any]:
    """Send or edit a screen; optionally answer a callback query."""
    pair = await _client_for_user(db, user_id)
    if pair is None:
        return {"ok": False, "detail": "Telegram not configured"}
    client, chat_id = pair

    if callback_id:
        try:
            await client.answer_callback_query(callback_id, text=callback_toast or "")
        except TelegramClientError as exc:
            logger.debug("answerCallbackQuery failed: %s", exc)

    try:
        if screen.edit and message_id is not None:
            result = await client.edit_message_text(
                chat_id,
                message_id,
                screen.text,
                parse_mode=screen.parse_mode,
                reply_markup=screen.keyboard,
            )
            return {"ok": True, "mode": "edit", "result": result}
        result = await client.send_message(
            chat_id,
            screen.text,
            parse_mode=screen.parse_mode,
            reply_markup=screen.keyboard,
        )
        return {"ok": True, "mode": "send", "result": result}
    except TelegramClientError as exc:
        # Fallback: send new message if edit fails (e.g. message too old / identical)
        logger.warning("render_screen edit/send failed (%s); trying send", exc)
        try:
            result = await client.send_message(
                chat_id,
                screen.text,
                parse_mode=screen.parse_mode,
                reply_markup=screen.keyboard,
            )
            return {"ok": True, "mode": "send_fallback", "result": result}
        except TelegramClientError as exc2:
            return {"ok": False, "detail": str(exc2)}


async def send_text(
    db: AsyncSession,
    user_id: str,
    text: str,
    *,
    keyboard: dict[str, Any] | None = None,
    parse_mode: str = "HTML",
) -> bool:
    """Convenience: send via notifier (supports reply_markup)."""
    notifier = await build_user_notifier(db, user_id, provider="telegram")
    if notifier is None:
        return False
    result = await notifier.send(
        NotifierMessage(text=text, parse_mode=parse_mode, reply_markup=keyboard)
    )
    return result.ok
