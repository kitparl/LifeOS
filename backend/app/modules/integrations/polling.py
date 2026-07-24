"""Long-polling fallback for Telegram inbound updates (dev / no public URL).

Started from lifespan only when TELEGRAM_POLLING_ENABLED=true.
Routes through the same CommandHandler as the webhook path.

When polling is enabled, any Telegram-side webhook is removed so getUpdates
can receive messages (Telegram forbids webhook + polling together).
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
_webhooks_cleared: set[str] = set()


async def _ensure_no_webhook(conn_id: str, user_id: str, bot_token: str) -> None:
    """Delete Telegram webhook (and clear DB secret) once per connection so polling works."""
    if conn_id in _webhooks_cleared:
        return
    client = TelegramClient(bot_token, timeout=15.0)
    try:
        info = await client.get_webhook_info()
        url = (info.get("url") or "") if isinstance(info, dict) else ""
        if url:
            logger.info("Polling: removing Telegram webhook for conn=%s (was %s)", conn_id, url)
            await client.delete_webhook(drop_pending_updates=False)
    except TelegramClientError as exc:
        logger.warning("Polling: get/delete webhook failed for conn=%s: %s", conn_id, exc)

    async with async_session_factory() as session:
        try:
            repo = IntegrationRepository(session)
            conn = await repo.get_by_id(user_id, conn_id)
            if conn is not None and conn.webhook_secret:
                conn.webhook_secret = None
                await session.commit()
            else:
                await session.rollback()
        except Exception:
            await session.rollback()
            logger.exception("Polling: failed to clear webhook_secret for conn=%s", conn_id)

    _webhooks_cleared.add(conn_id)


async def _process_update(user_id: str, chat_id: str, update: dict[str, Any]) -> None:
    msg = update.get("message") or update.get("edited_message") or {}
    if not isinstance(msg, dict):
        return
    chat = msg.get("chat") if isinstance(msg.get("chat"), dict) else {}
    incoming_chat = str(chat.get("id") or "")
    if incoming_chat != chat_id:
        logger.warning(
            "Polling: ignoring update from chat_id=%s (expected %s)",
            incoming_chat,
            chat_id,
        )
        return
    text = str(msg.get("text") or "").strip()
    if not text:
        return
    logger.info("Polling: handling command from user=%s text=%r", user_id, text[:80])
    async with async_session_factory() as session:
        try:
            reply = await handle_command(session, user_id, text)
            notifier = await build_user_notifier(session, user_id, provider="telegram")
            if notifier is None:
                logger.warning("Polling: no notifier for user=%s", user_id)
            else:
                result = await notifier.send(NotifierMessage(text=reply, parse_mode="HTML"))
                if not result.ok:
                    # Retry without HTML in case parse_mode rejected the body
                    logger.warning("Polling: HTML send failed (%s); retrying plain", result.detail)
                    await notifier.send(NotifierMessage(text=reply, parse_mode=""))
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
                await _ensure_no_webhook(conn.id, conn.user_id, cfg.bot_token)
                offset = _offsets.get(conn.id)
                client = TelegramClient(cfg.bot_token, timeout=25.0)
                try:
                    updates = await client.get_updates(limit=20, timeout=10, offset=offset)
                except TelegramClientError as exc:
                    logger.warning("getUpdates failed for conn=%s: %s", conn.id, exc)
                    # Conflict: webhook still set — force clear next iteration
                    if "webhook" in str(exc).lower() or "Conflict" in str(exc):
                        _webhooks_cleared.discard(conn.id)
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
    _webhooks_cleared.clear()
