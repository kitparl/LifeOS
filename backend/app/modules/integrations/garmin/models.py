from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, new_id
from app.core.timezone import utc_now

JOB_QUEUED = "queued"
JOB_RUNNING = "running"
JOB_FINISHED = "finished"
JOB_FAILED = "failed"
JOB_INTERRUPTED = "interrupted"
ACTIVE_STATUSES = (JOB_QUEUED, JOB_RUNNING)


class GarminImportJob(Base):
    """One import of uploaded Garmin files. The list of these rows is the sync log; they are never purged."""

    __tablename__ = "garmin_import_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=JOB_QUEUED)
    range_mode: Mapped[str] = mapped_column(String(8), nullable=False, default="12m")
    files_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outside_range: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    not_activity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    runs_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    runs_matched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    error: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
