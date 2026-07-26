"""Assignment lifecycle — append-only history, future multi-assignee ready."""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import (
    TASK_ASSIGNED,
    TASK_ASSIGNMENT_ACCEPTED,
    TASK_ASSIGNMENT_CANCELLED,
    TASK_ASSIGNMENT_REJECTED,
    TASK_REASSIGNED,
    EntityCreated,
    event_bus,
)
from app.modules.auth.repository import UserRepository
from app.modules.tasks.activity_service import ActivityService
from app.modules.tasks.models import Task, TaskAssignment
from app.modules.tasks.permissions import TaskPermissions

# Simple in-process rate limit for assignment mutations (SECURITY-11)
_assign_hits: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW_S = 60.0
_RATE_MAX = 30


def _check_rate(user_id: str) -> None:
    now = time.monotonic()
    hits = _assign_hits[user_id]
    _assign_hits[user_id] = [t for t in hits if now - t < _RATE_WINDOW_S]
    if len(_assign_hits[user_id]) >= _RATE_MAX:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many assignment actions")
    _assign_hits[user_id].append(now)


ACTIVE_STATUSES = ("pending", "accepted")


class AssignmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.activity = ActivityService(db)
        self.perms = TaskPermissions(db)
        self.auth = UserRepository(db)

    async def get_active(self, task_id: str) -> TaskAssignment | None:
        result = await self.db.execute(
            select(TaskAssignment)
            .where(
                TaskAssignment.task_id == task_id,
                TaskAssignment.status.in_(ACTIVE_STATUSES),
            )
            .order_by(TaskAssignment.assigned_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_for_task(self, task_id: str) -> list[TaskAssignment]:
        result = await self.db.execute(
            select(TaskAssignment)
            .where(TaskAssignment.task_id == task_id)
            .order_by(TaskAssignment.assigned_at.desc())
        )
        return list(result.scalars().all())

    async def create_self_assignment(self, task: Task, actor_id: str) -> TaskAssignment:
        """Default on create: auto-accepted, no notification."""
        row = TaskAssignment(
            task_id=task.id,
            assignee_user_id=actor_id,
            assigned_by_user_id=actor_id,
            status="accepted",
            assigned_at=datetime.now(timezone.utc),
            accepted_at=datetime.now(timezone.utc),
        )
        self.db.add(row)
        await self.db.flush()
        await self.activity.log(task.id, actor_id, "assign", field="assignee", new_value=actor_id, metadata={"self": True})
        return row

    async def assign(
        self,
        task: Task,
        actor_id: str,
        *,
        assignee_user_id: str | None = None,
        assignee_username: str | None = None,
        reason: str | None = None,
    ) -> TaskAssignment:
        _check_rate(actor_id)
        await self.perms.require(actor_id, task, "assign")

        if assignee_username:
            user = await self.auth.get_by_username(assignee_username)
            if user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found")
            assignee_user_id = user.id
        if not assignee_user_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="assignee_user_id or assignee_username required")

        # Self-assign → accepted, no notify
        is_self = assignee_user_id == actor_id
        new_status = "accepted" if is_self else "pending"
        now = datetime.now(timezone.utc)

        old_active = await self._close_active(task.id, now, new_status="reassigned")

        row = TaskAssignment(
            task_id=task.id,
            assignee_user_id=assignee_user_id,
            assigned_by_user_id=actor_id,
            status=new_status,
            reason=reason,
            assigned_at=now,
            accepted_at=now if is_self else None,
        )
        self.db.add(row)
        await self.db.flush()
        if old_active:
            old_active.superseded_by_id = row.id
            await self.db.flush()

        await self.activity.log(
            task.id,
            actor_id,
            "reassign" if old_active else "assign",
            field="assignee",
            old_value=old_active.assignee_user_id if old_active else None,
            new_value=assignee_user_id,
            metadata={"reason": reason} if reason else None,
        )

        # Notify new assignee (skip self-assign spam)
        if not is_self:
            event_type = TASK_REASSIGNED if old_active else TASK_ASSIGNED
            await event_bus.emit(
                self.db,
                EntityCreated(
                    event_type=event_type,
                    user_id=assignee_user_id,
                    entity_id=task.id,
                    title=task.title,
                    when=row.id,
                    module="tasks",
                ),
            )
        # Always notify previous assignee when someone else takes over (incl. owner take-back)
        if old_active and old_active.assignee_user_id != assignee_user_id:
            await event_bus.emit(
                self.db,
                EntityCreated(
                    event_type=TASK_REASSIGNED,
                    user_id=old_active.assignee_user_id,
                    entity_id=task.id,
                    title=task.title,
                    when="previous",
                    module="tasks",
                ),
            )
        return row

    async def accept(self, task: Task, assignment_id: str, actor_id: str) -> TaskAssignment:
        _check_rate(actor_id)
        row = await self._get_assignment(task.id, assignment_id)
        if row.assignee_user_id != actor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        if row.status != "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assignment is not pending")
        row.status = "accepted"
        row.accepted_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.activity.log(task.id, actor_id, "accept", field="assignment_status", old_value="pending", new_value="accepted")
        await event_bus.emit(
            self.db,
            EntityCreated(
                event_type=TASK_ASSIGNMENT_ACCEPTED,
                user_id=task.user_id,
                entity_id=task.id,
                title=task.title,
                module="tasks",
            ),
        )
        return row

    async def reject(
        self, task: Task, assignment_id: str, actor_id: str, *, reason: str | None = None
    ) -> TaskAssignment:
        _check_rate(actor_id)
        row = await self._get_assignment(task.id, assignment_id)
        if row.assignee_user_id != actor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        if row.status != "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assignment is not pending")
        now = datetime.now(timezone.utc)
        row.status = "rejected"
        row.rejected_at = now
        row.reason = reason
        await self.db.flush()
        await self.activity.log(
            task.id,
            actor_id,
            "reject",
            field="assignment_status",
            old_value="pending",
            new_value="rejected",
            metadata={"reason": reason} if reason else None,
        )
        # Fallback: auto-accepted assignment to owner
        fallback = TaskAssignment(
            task_id=task.id,
            assignee_user_id=task.user_id,
            assigned_by_user_id=actor_id,
            status="accepted",
            reason=f"Fallback after rejection: {reason}" if reason else "Fallback after rejection",
            assigned_at=now,
            accepted_at=now,
        )
        self.db.add(fallback)
        row.superseded_by_id = None  # rejected, not superseded by reassign chain
        await self.db.flush()
        await self.activity.log(task.id, actor_id, "assign", field="assignee", new_value=task.user_id, metadata={"fallback": True})
        await event_bus.emit(
            self.db,
            EntityCreated(
                event_type=TASK_ASSIGNMENT_REJECTED,
                user_id=task.user_id,
                entity_id=task.id,
                title=task.title,
                when=reason,
                module="tasks",
            ),
        )
        return row

    async def cancel(self, task: Task, assignment_id: str, actor_id: str) -> TaskAssignment:
        _check_rate(actor_id)
        await self.perms.require(actor_id, task, "assign")
        row = await self._get_assignment(task.id, assignment_id)
        if row.status not in ACTIVE_STATUSES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assignment is not active")
        previous_assignee = row.assignee_user_id
        row.status = "cancelled"
        row.cancelled_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.activity.log(task.id, actor_id, "cancel", field="assignment_status", new_value="cancelled")
        # Ensure owner is active assignee
        active = await self.get_active(task.id)
        if active is None:
            await self.create_self_assignment(task, task.user_id)
        # Notify previous assignee (unless they are the owner taking it back themselves)
        if previous_assignee != actor_id:
            await event_bus.emit(
                self.db,
                EntityCreated(
                    event_type=TASK_ASSIGNMENT_CANCELLED,
                    user_id=previous_assignee,
                    entity_id=task.id,
                    title=task.title,
                    module="tasks",
                ),
            )
        return row

    async def mark_completed_for_task(self, task: Task) -> None:
        result = await self.db.execute(
            select(TaskAssignment).where(
                TaskAssignment.task_id == task.id,
                TaskAssignment.status.in_(ACTIVE_STATUSES),
            )
        )
        now = datetime.now(timezone.utc)
        for row in result.scalars().all():
            row.status = "completed"
            row.completed_at = now
        await self.db.flush()

    async def _close_active(self, task_id: str, now: datetime, *, new_status: str) -> TaskAssignment | None:
        active = await self.get_active(task_id)
        if active is None:
            return None
        active.status = new_status
        if new_status == "cancelled":
            active.cancelled_at = now
        await self.db.flush()
        return active

    async def _get_assignment(self, task_id: str, assignment_id: str) -> TaskAssignment:
        result = await self.db.execute(
            select(TaskAssignment).where(
                TaskAssignment.id == assignment_id,
                TaskAssignment.task_id == task_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
        return row


async def load_task_for_actor(db: AsyncSession, task_id: str, user_id: str) -> Task:
    """Load non-deleted task if actor is owner, assignee, or watcher; else 404."""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id, Task.deleted_at.is_(None))
        .options(selectinload(Task.subtasks), selectinload(Task.assignments))
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    role = await TaskPermissions(db).resolve_role(user_id, task)
    if role.value == "none":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task
