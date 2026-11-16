from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, new_id
from app.core.timezone import utc_now


class Activity(Base):
    """One recorded activity of any sport from any source (the activity log)."""

    __tablename__ = "activities"
    __table_args__ = (
        UniqueConstraint("user_id", "source", "external_id", name="uq_activities_user_source_external"),
        Index("ix_activities_user_start", "user_id", "start_time_utc"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    external_id: Mapped[str] = mapped_column(String(80), nullable=False)
    sport: Mapped[str] = mapped_column(String(32), nullable=False)
    start_time_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    elapsed_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    timer_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_gain_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_cadence: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_speed_mps: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    device: Mapped[str | None] = mapped_column(String(64), nullable=True)
    training_effect_aerobic: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_effect_anaerobic: Mapped[float | None] = mapped_column(Float, nullable=True)
    laps_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    splits_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    polyline: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ActivitySeries(Base):
    """Per-sample channels of an activity as gzip JSON; loaded only when a detail page needs charts."""

    __tablename__ = "activity_series"

    activity_id: Mapped[str] = mapped_column(String(36), ForeignKey("activities.id"), primary_key=True)
    data_gz: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
