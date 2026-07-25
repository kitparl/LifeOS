"""Audit log for scheduled Telegram reports and reminder dispatches."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

REPORT_JOB_TYPES = (
    "morning",
    "midday",
    "night",
    "weekly",
    "ai_briefing",
    "birthday_reminder",
    "immutable_reminder",
    "routine_reminder",
)

REPORT_STATUSES = ("started", "sent", "skipped", "failed")
SKIP_REASONS = ("telegram_disabled", "prefs_off", "empty", "duplicate", "no_api_key")


class ScheduledReportRun(Base):
    """One row per triggered cron / reminder attempt per user."""

    __tablename__ = "scheduled_report_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    connection_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    job_id: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="started", index=True)
    skip_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sections_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(191), nullable=True, unique=True)
    message_chars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_scheduled_report_runs_user_job_created", "user_id", "job_type", "created_at"),
        Index("ix_scheduled_report_runs_status_created", "status", "created_at"),
        UniqueConstraint("dedupe_key", name="uq_scheduled_report_runs_dedupe_key"),
    )
