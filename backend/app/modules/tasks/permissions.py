"""Per-task authorization (SECURITY-08 / SECURITY-11)."""

from __future__ import annotations

from enum import Enum

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tasks.models import Task, TaskAssignment, TaskWatcher


class TaskRole(str, Enum):
    OWNER = "owner"
    ASSIGNEE = "assignee"
    WATCHER = "watcher"
    NONE = "none"


# Actions that require ownership
OWNER_ACTIONS = frozenset(
    {
        "edit",
        "assign",
        "manage_watchers",
        "manage_tags",
        "archive",
        "delete",
        "change_priority",
        "change_due",
    }
)

# Actions assignees (accepted) may perform
ASSIGNEE_ACTIONS = frozenset({"view", "change_status", "add_note", "accept_reject"})

# Watchers may only view + read history
WATCHER_ACTIONS = frozenset({"view", "view_history"})


class TaskPermissions:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve_role(self, user_id: str, task: Task) -> TaskRole:
        if task.user_id == user_id:
            return TaskRole.OWNER
        active = await self.db.execute(
            select(TaskAssignment.id).where(
                TaskAssignment.task_id == task.id,
                TaskAssignment.assignee_user_id == user_id,
                TaskAssignment.status.in_(("pending", "accepted")),
            ).limit(1)
        )
        if active.scalar_one_or_none():
            return TaskRole.ASSIGNEE
        watcher = await self.db.execute(
            select(TaskWatcher.id).where(
                TaskWatcher.task_id == task.id,
                TaskWatcher.user_id == user_id,
            ).limit(1)
        )
        if watcher.scalar_one_or_none():
            return TaskRole.WATCHER
        return TaskRole.NONE

    def can(self, role: TaskRole, action: str) -> bool:
        if role == TaskRole.OWNER:
            return True
        if role == TaskRole.ASSIGNEE:
            return action in ASSIGNEE_ACTIONS or action in WATCHER_ACTIONS
        if role == TaskRole.WATCHER:
            return action in WATCHER_ACTIONS
        return False

    async def require(self, user_id: str, task: Task, action: str) -> TaskRole:
        role = await self.resolve_role(user_id, task)
        if not self.can(role, action):
            # SECURITY-08: 404 for none to avoid existence leaks; 403 for known participants lacking permission
            if role == TaskRole.NONE:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return role

    def permission_flags(self, role: TaskRole) -> dict[str, bool]:
        return {
            "can_edit": self.can(role, "edit"),
            "can_assign": self.can(role, "assign"),
            "can_change_status": self.can(role, "change_status"),
            "can_add_note": self.can(role, "add_note"),
            "can_manage_watchers": self.can(role, "manage_watchers"),
            "can_manage_tags": self.can(role, "manage_tags"),
            "can_archive": self.can(role, "archive"),
            "can_delete": self.can(role, "delete"),
            "role": role.value,
        }
