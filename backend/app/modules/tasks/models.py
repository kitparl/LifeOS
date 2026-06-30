import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

TASK_STATUSES = ("pending", "in_progress", "completed", "cancelled")
TASK_PRIORITIES = ("low", "medium", "high", "urgent")
TASK_RECURRENCE = ("none", "daily", "weekly", "monthly")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=True)
    goal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("goals.id"), nullable=True)
    recurrence: Mapped[str] = mapped_column(String(16), nullable=False, default="none")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    subtasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys="Task.parent_id",
    )
    parent: Mapped["Task | None"] = relationship(
        "Task", back_populates="subtasks", remote_side="Task.id", foreign_keys="Task.parent_id"
    )

    @property
    def tags(self) -> list[str]:
        try:
            return json.loads(self.tags_json)
        except json.JSONDecodeError:
            return []

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self.tags_json = json.dumps(value)
