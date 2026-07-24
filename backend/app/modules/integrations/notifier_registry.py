"""Registry that builds a Notifier for a user/provider without callers knowing Telegram specifics."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.notifier import Notifier, TelegramNotifier
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.telegram_client import TelegramClient
from app.modules.integrations.telegram_config import parse_config

logger = logging.getLogger(__name__)

NotifierBuilder: TypeAlias = Callable[[AsyncSession, str], Awaitable[Notifier | None]]


async def _build_telegram(db: AsyncSession, user_id: str) -> Notifier | None:
    repo = IntegrationRepository(db)
    conn = await repo.get_by_provider(user_id, "telegram")
    if conn is None or not conn.enabled:
        return None
    cfg = parse_config(conn.config_json)
    if cfg is None:
        return None
    client = TelegramClient(cfg.bot_token)
    return TelegramNotifier(client, cfg.chat_id)


# Register additional task-specific bots / channels by adding builders here.
NOTIFIER_BUILDERS: dict[str, NotifierBuilder] = {
    "telegram": _build_telegram,
}


async def build_user_notifier(
    db: AsyncSession,
    user_id: str,
    provider: str = "telegram",
) -> Notifier | None:
    """Resolve an enabled notifier for the user, or None if not configured."""
    builder = NOTIFIER_BUILDERS.get(provider)
    if builder is None:
        logger.debug("No notifier builder for provider=%s", provider)
        return None
    try:
        return await builder(db, user_id)
    except Exception:
        # Fail closed: never raise secrets; callers treat None/failure as "not sent"
        logger.exception("Failed to build notifier for provider=%s", provider)
        return None
