"""Drain pending_notifications after commit via the Notifier registry."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.modules.integrations.notifier import NotifierMessage
from app.modules.integrations.notifier_registry import build_user_notifier
from app.modules.integrations.outbox_repository import OutboxRepository

logger = logging.getLogger(__name__)


def _parse_markup(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except (TypeError, ValueError):
        return None


class NotificationDispatcher:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OutboxRepository(db)

    async def dispatch_pending(self, *, limit: int = 50) -> int:
        """Send up to `limit` pending notifications. Returns count sent successfully."""
        rows = await self.repo.fetch_dispatchable(limit=limit)
        sent = 0
        for row in rows:
            try:
                notifier = await build_user_notifier(self.db, row.user_id, provider=row.channel)
                if notifier is None:
                    await self.repo.mark_failed(row, "Notifier not configured or disabled")
                    continue
                markup = _parse_markup(getattr(row, "reply_markup_json", None))
                result = await notifier.send(
                    NotifierMessage(
                        text=row.text,
                        parse_mode=row.parse_mode,
                        reply_markup=markup,
                    )
                )
                if result.ok:
                    await self.repo.mark_sent(row)
                    sent += 1
                else:
                    await self.repo.mark_failed(row, result.detail)
            except Exception as exc:
                logger.exception("Dispatcher error for notification %s", row.id)
                await self.repo.mark_failed(row, str(exc) or type(exc).__name__)
        await self.db.commit()
        return sent


async def dispatch_pending_notifications(*, limit: int = 50) -> int:
    """Open a fresh session and drain the outbox (safe for after_commit / scheduler)."""
    async with async_session_factory() as session:
        try:
            count = await NotificationDispatcher(session).dispatch_pending(limit=limit)
            return count
        except Exception:
            await session.rollback()
            logger.exception("dispatch_pending_notifications failed")
            return 0
