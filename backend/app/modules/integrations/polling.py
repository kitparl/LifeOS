"""Long-polling fallback for Telegram inbound updates (dev / no public URL).

Started from lifespan only when TELEGRAM_POLLING_ENABLED=true.
Routes through the same update_router as the webhook path.

When polling is enabled, any Telegram-side webhook is removed so getUpdates
can receive messages (Telegram forbids webhook + polling together).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.core.database import async_session_factory
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.telegram.update_router import route_update
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
    async with async_session_factory() as session:
        try:
            result = await route_update(session, user_id, chat_id, update)
            await session.commit()
            logger.info("Polling: routed update user=%s result=%s", user_id, result)
        except Exception:
            await session.rollback()
            logger.exception("Polling update handling failed")


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
