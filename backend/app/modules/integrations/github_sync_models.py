import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

SYNC_STATUS_NEVER = "never_synced"
SYNC_STATUS_SYNCING = "syncing"
SYNC_STATUS_SYNCED = "synced"
SYNC_STATUS_UNCHANGED = "unchanged"
SYNC_STATUS_FAILED = "failed"


class GitHubSyncState(Base):
    __tablename__ = "github_sync_state"
    __table_args__ = (UniqueConstraint("user_id", "section_id", name="uq_github_sync_user_section"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    section_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    md_path: Mapped[str] = mapped_column(String(500), nullable=False)
    md_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assets_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    remote_commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(16), nullable=False, default=SYNC_STATUS_NEVER)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
