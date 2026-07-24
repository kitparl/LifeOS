"""Long-polling fallback for Telegram inbound updates (dev / no public URL).

Started from lifespan only when TELEGRAM_POLLING_ENABLED=true.
Routes through the same CommandHandler as the webhook path.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.core.database import async_session_factory
from app.modules.integrations.command_handler import handle_command
from app.modules.integrations.notifier import NotifierMessage
from app.modules.integrations.notifier_registry import build_user_notifier
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.telegram_client import TelegramClient, TelegramClientError
from app.modules.integrations.telegram_config import parse_config

logger = logging.getLogger(__name__)

_poll_task: asyncio.Task | None = None
_offsets: dict[str, int] = {}  # connection_id -> next offset


async def _process_update(user_id: str, chat_id: str, update: dict[str, Any]) -> None:
    msg = update.get("message") or update.get("edited_message") or {}
    if not isinstance(msg, dict):
        return
    chat = msg.get("chat") if isinstance(msg.get("chat"), dict) else {}
    incoming_chat = str(chat.get("id") or "")
    if incoming_chat != chat_id:
        logger.warning("Polling: ignoring update from unknown chat")
        return
    text = str(msg.get("text") or "").strip()
    if not text:
        return
    async with async_session_factory() as session:
        try:
            reply = await handle_command(session, user_id, text)
            notifier = await build_user_notifier(session, user_id, provider="telegram")
            if notifier is not None:
                await notifier.send(NotifierMessage(text=reply, parse_mode="HTML"))
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Polling command handling failed")


async def _poll_loop() -> None:
    logger.info("Telegram long-polling started")
    while True:
        try:
            async with async_session_factory() as session:
                repo = IntegrationRepository(session)
                conns = await repo.list_enabled_telegram()
            for conn in conns:
                cfg = parse_config(conn.config_json)
                if cfg is None:
                    continue
                # Skip connections that have an active webhook (Telegram forbids both)
                if conn.webhook_secret:
                    continue
                offset = _offsets.get(conn.id)
                client = TelegramClient(cfg.bot_token, timeout=25.0)
                try:
                    updates = await client.get_updates(limit=20, timeout=10, offset=offset)
                except TelegramClientError as exc:
                    logger.warning("getUpdates failed for conn=%s: %s", conn.id, exc)
                    continue
                for update in updates:
                    update_id = update.get("update_id")
                    if isinstance(update_id, int):
                        _offsets[conn.id] = update_id + 1
                    await _process_update(conn.user_id, cfg.chat_id, update)
        except asyncio.CancelledError:
            logger.info("Telegram long-polling stopped")
            raise
        except Exception:
            logger.exception("Telegram poll loop error")
            await asyncio.sleep(5)
        await asyncio.sleep(1)


def start_polling() -> None:
    global _poll_task
    if _poll_task is not None and not _poll_task.done():
        return
    _poll_task = asyncio.create_task(_poll_loop(), name="telegram-polling")


async def stop_polling() -> None:
    global _poll_task
    if _poll_task is None:
        return
    _poll_task.cancel()
    try:
        await _poll_task
    except asyncio.CancelledError:
        pass
    _poll_task = None
