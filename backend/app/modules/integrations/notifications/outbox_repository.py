"""Repository for pending_notifications outbox rows."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.outbox_models import FAILED, PENDING, SENT, PendingNotification


class OutboxRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def enqueue(
        self,
        user_id: str,
        text: str,
        *,
        channel: str = "telegram",
        parse_mode: str = "HTML",
        reply_markup: dict[str, Any] | None = None,
    ) -> PendingNotification:
        row = PendingNotification(
            user_id=user_id,
            channel=channel,
            text=text,
            parse_mode=parse_mode,
            reply_markup_json=json.dumps(reply_markup) if reply_markup else None,
            status=PENDING,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def fetch_dispatchable(self, *, limit: int = 50) -> list[PendingNotification]:
        result = await self.db.execute(
            select(PendingNotification)
            .where(
                and_(
                    PendingNotification.status == PENDING,
                    PendingNotification.attempts < PendingNotification.max_attempts,
                )
            )
            .order_by(PendingNotification.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_sent(self, row: PendingNotification) -> None:
        row.status = SENT
        row.sent_at = datetime.now(timezone.utc)
        row.attempts += 1
        row.last_error = None
        await self.db.flush()

    async def mark_failed(self, row: PendingNotification, error: str) -> None:
        row.attempts += 1
        row.last_error = (error or "send failed")[:2000]
        if row.attempts >= row.max_attempts:
            row.status = FAILED
        await self.db.flush()
