import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

GOAL_CATEGORIES = ("career", "running", "finance", "learning", "personal", "health")
GOAL_STATUSES = ("active", "archived", "completed")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="personal")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("goals.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    milestones: Mapped[list["GoalMilestone"]] = relationship(
        "GoalMilestone", back_populates="goal", cascade="all, delete-orphan", order_by="GoalMilestone.sort_order"
    )


class GoalMilestone(Base):
    __tablename__ = "goal_milestones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id: Mapped[str] = mapped_column(String(36), ForeignKey("goals.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    goal: Mapped["Goal"] = relationship("Goal", back_populates="milestones")
