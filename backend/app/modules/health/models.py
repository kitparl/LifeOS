from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, new_id
from app.core.timezone import utc_now


def _int() -> Mapped[int | None]:
    return mapped_column(Integer, nullable=True)


def _float() -> Mapped[float | None]:
    return mapped_column(Float, nullable=True)


class HealthDay(Base):
    """One row per user, date and source. Column names equal the keys of the metric catalogue."""

    __tablename__ = "health_days"
    __table_args__ = (UniqueConstraint("user_id", "date", "source", name="uq_health_days_user_date_source"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(16), nullable=False)

    sleep_total_min: Mapped[int | None] = _int()
    sleep_deep_min: Mapped[int | None] = _int()
    sleep_light_min: Mapped[int | None] = _int()
    sleep_rem_min: Mapped[int | None] = _int()
    sleep_awake_min: Mapped[int | None] = _int()
    sleep_score: Mapped[int | None] = _int()
    bed_time_min: Mapped[int | None] = _int()
    wake_time_min: Mapped[int | None] = _int()
    resting_hr: Mapped[int | None] = _int()
    min_hr: Mapped[int | None] = _int()
    max_hr: Mapped[int | None] = _int()
    avg_hr: Mapped[int | None] = _int()
    hrv_ms: Mapped[float | None] = _float()
    stress_avg: Mapped[int | None] = _int()
    stress_max: Mapped[int | None] = _int()
    body_battery_high: Mapped[int | None] = _int()
    body_battery_low: Mapped[int | None] = _int()
    steps: Mapped[int | None] = _int()
    distance_km: Mapped[float | None] = _float()
    floors: Mapped[int | None] = _int()
    active_calories: Mapped[int | None] = _int()
    total_calories: Mapped[int | None] = _int()
    intensity_min_moderate: Mapped[int | None] = _int()
    intensity_min_vigorous: Mapped[int | None] = _int()
    respiration_avg: Mapped[float | None] = _float()
    spo2_avg: Mapped[float | None] = _float()
    spo2_min: Mapped[float | None] = _float()
    vo2_max: Mapped[float | None] = _float()

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class HealthMeasurement(Base):
    """A single reading: weight, body composition or blood pressure."""

    __tablename__ = "health_measurements"
    __table_args__ = (
        UniqueConstraint("user_id", "source", "external_id", name="uq_health_measurements_external"),
        Index("ix_health_measurements_user_kind_time", "user_id", "kind", "measured_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    values_json: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")
    external_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
