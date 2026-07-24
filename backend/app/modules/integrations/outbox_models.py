"""Transactional outbox for deferred notification delivery.

Rows are written in the same DB session as the entity create, so a rolled-back
transaction never notifies. A dispatcher drains pending rows after commit.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

PENDING = "pending"
SENT = "sent"
FAILED = "failed"


class PendingNotification(Base):
    __tablename__ = "pending_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="telegram")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    parse_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="HTML")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=PENDING, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
