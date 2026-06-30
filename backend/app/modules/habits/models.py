import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

HABIT_FREQUENCIES = ("daily", "weekly", "monthly")


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False, default="daily")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    logs: Mapped[list["HabitLog"]] = relationship(
        "HabitLog", back_populates="habit", cascade="all, delete-orphan", order_by="HabitLog.log_date.desc()"
    )


class HabitLog(Base):
    __tablename__ = "habit_logs"
    __table_args__ = (UniqueConstraint("habit_id", "log_date", name="uq_habit_log_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    habit_id: Mapped[str] = mapped_column(String(36), ForeignKey("habits.id", ondelete="CASCADE"), index=True)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    habit: Mapped["Habit"] = relationship("Habit", back_populates="logs")
