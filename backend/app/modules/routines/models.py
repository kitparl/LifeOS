import json
import uuid
from datetime import date, datetime, time, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.habits.models import Habit

# Life areas this schedule is meant to protect time for.
ROUTINE_AREAS = (
    "dsa",
    "gym",
    "running",
    "learning",
    "communication",
    "book",
    "other",
)

# Calendar categories a block can map into.
ROUTINE_CATEGORIES = ("personal", "task", "running", "bill", "learning")

routine_block_habits = Table(
    "routine_block_habits",
    Base.metadata,
    Column("block_id", String(36), ForeignKey("routine_blocks.id", ondelete="CASCADE"), primary_key=True),
    Column("habit_id", String(36), ForeignKey("habits.id", ondelete="CASCADE"), primary_key=True),
)


class Routine(Base):
    """Named day schedule template (e.g. Weekday Focus) with timed blocks."""

    __tablename__ = "routines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON list of Python weekdays: 0=Mon … 6=Sun
    days_of_week_json: Mapped[str] = mapped_column(Text, nullable=False, default="[0,1,2,3,4]")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Kolkata")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    skip_dates_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    blocks: Mapped[list["RoutineBlock"]] = relationship(
        "RoutineBlock",
        back_populates="routine",
        cascade="all, delete-orphan",
        order_by="RoutineBlock.sort_order.asc()",
    )

    @property
    def days_of_week(self) -> list[int]:
        try:
            raw = json.loads(self.days_of_week_json)
            if isinstance(raw, list):
                return [int(d) for d in raw if 0 <= int(d) <= 6]
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        return [0, 1, 2, 3, 4]

    @days_of_week.setter
    def days_of_week(self, value: list[int]) -> None:
        cleaned = sorted({int(d) for d in value if 0 <= int(d) <= 6})
        self.days_of_week_json = json.dumps(cleaned or [0, 1, 2, 3, 4])

    @property
    def skip_dates(self) -> list[str]:
        try:
            raw = json.loads(self.skip_dates_json or "[]")
            if isinstance(raw, list):
                return sorted({str(d) for d in raw if d})
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        return []

    @skip_dates.setter
    def skip_dates(self, value: list[str] | list[date]) -> None:
        cleaned: list[str] = []
        for d in value or []:
            if isinstance(d, date):
                cleaned.append(d.isoformat())
            else:
                s = str(d).strip()
                if s:
                    cleaned.append(s[:10])
        self.skip_dates_json = json.dumps(sorted(set(cleaned)))


class RoutineBlock(Base):
    """A timed slot inside a routine (e.g. DSA 08:00–10:00)."""

    __tablename__ = "routine_blocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    routine_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("routines.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    area: Mapped[str] = mapped_column(String(32), nullable=False, default="other")
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="personal")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    routine: Mapped["Routine"] = relationship("Routine", back_populates="blocks")
    habits: Mapped[list["Habit"]] = relationship(
        "Habit",
        secondary=routine_block_habits,
        lazy="selectin",
    )


class RoutineAreaOption(Base):
    """User-defined reusable life-area labels for routine blocks."""

    __tablename__ = "routine_areas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_routine_areas_user_name"),)


class RoutineCategoryOption(Base):
    """User-defined reusable calendar categories for routine blocks."""

    __tablename__ = "routine_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_routine_categories_user_name"),)
