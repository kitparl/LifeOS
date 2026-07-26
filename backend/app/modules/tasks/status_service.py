"""Task status changes with history."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tasks.activity_service import ActivityService
from app.modules.tasks.models import Task, TaskStatusHistory
from app.modules.tasks.status_utils import normalize_task_status


class StatusService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.activity = ActivityService(db)

    async def change_status(
        self,
        task: Task,
        actor_user_id: str,
        new_status: str,
        *,
        reason: str | None = None,
    ) -> Task:
        normalized = normalize_task_status(new_status)
        assert normalized is not None
        if task.status == normalized:
            return task
        old = task.status
        history = TaskStatusHistory(
            task_id=task.id,
            from_status=old,
            to_status=normalized,
            changed_by_user_id=actor_user_id,
            reason=reason,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(history)
        task.status = normalized
        task.version = (task.version or 1) + 1
        if normalized == "completed":
            task.completed_at = datetime.now(timezone.utc)
        elif old == "completed":
            task.completed_at = None
        await self.activity.log(
            task.id,
            actor_user_id,
            "status_change",
            field="status",
            old_value=old,
            new_value=normalized,
            metadata={"reason": reason} if reason else None,
        )
        await self.db.flush()
        return task

    async def list_history(
        self, task_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[TaskStatusHistory]:
        result = await self.db.execute(
            select(TaskStatusHistory)
            .where(TaskStatusHistory.task_id == task_id)
            .order_by(TaskStatusHistory.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
