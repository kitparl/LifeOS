from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.tasks.status_utils import normalize_task_status

TaskStatus = Literal["pending", "in_progress", "hold", "delayed", "completed", "cancelled", "done"]
TaskPriority = Literal["low", "medium", "high", "urgent"]
TaskRecurrence = Literal["none", "daily", "weekly", "monthly"]
TaskScope = Literal["owned", "assigned_to_me", "all"]
AssignmentStatus = Literal["pending", "accepted", "rejected", "cancelled", "reassigned", "completed"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = "pending"
    priority: TaskPriority = "medium"
    category: str | None = Field(default=None, max_length=64)
    tags: list[str] = Field(default_factory=list, max_length=50)
    due_date: datetime | None = None
    parent_id: str | None = None
    goal_id: str | None = None
    recurrence: TaskRecurrence = "none"
    assignee_username: str | None = Field(default=None, max_length=30)
    assignee_user_id: str | None = Field(default=None, max_length=36)

    @field_validator("status", mode="before")
    @classmethod
    def _status(cls, v):
        return normalize_task_status(v) if v is not None else v

    @field_validator("tags")
    @classmethod
    def _tags(cls, v: list[str]) -> list[str]:
        return [t.strip()[:64] for t in v if t and t.strip()][:50]


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    category: str | None = Field(default=None, max_length=64)
    tags: list[str] | None = None
    due_date: datetime | None = None
    goal_id: str | None = None
    recurrence: TaskRecurrence | None = None
    version: int | None = None
    status_reason: str | None = Field(default=None, max_length=500)

    @field_validator("status", mode="before")
    @classmethod
    def _status(cls, v):
        return normalize_task_status(v) if v is not None else v


class SubtaskResponse(BaseModel):
    id: str
    title: str
    status: str
    priority: str
    completed_at: datetime | None
    assigned_to: str | None = None
    assignment_status: str | None = None
    assignee_username: str | None = None

    model_config = {"from_attributes": True}


class TaskPermissionsFlags(BaseModel):
    can_edit: bool = False
    can_assign: bool = False
    can_change_status: bool = False
    can_add_note: bool = False
    can_manage_watchers: bool = False
    can_manage_tags: bool = False
    can_archive: bool = False
    can_delete: bool = False
    role: str = "none"


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str | None
    status: str
    priority: str
    category: str | None
    tags: list[str]
    due_date: datetime | None
    parent_id: str | None
    goal_id: str | None
    recurrence: str
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    subtasks: list[SubtaskResponse] = []
    # Additive fields
    archived_at: datetime | None = None
    version: int = 1
    assigned_to: str | None = None
    assigned_by: str | None = None
    assignment_status: str | None = None
    assignment_id: str | None = None
    accepted_at: datetime | None = None
    rejected_at: datetime | None = None
    assignee_username: str | None = None
    permissions: TaskPermissionsFlags | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(
        cls,
        task,
        *,
        assignment=None,
        permissions: dict | None = None,
        assignee_username: str | None = None,
        subtasks: list[SubtaskResponse] | None = None,
    ) -> "TaskResponse":
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            category=task.category,
            tags=task.tags,
            due_date=task.due_date,
            parent_id=task.parent_id,
            goal_id=task.goal_id,
            recurrence=task.recurrence,
            completed_at=task.completed_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
            subtasks=subtasks
            if subtasks is not None
            else [SubtaskResponse.model_validate(s) for s in (task.subtasks or []) if s.deleted_at is None],
            archived_at=getattr(task, "archived_at", None),
            version=getattr(task, "version", 1) or 1,
            assigned_to=assignment.assignee_user_id if assignment else None,
            assigned_by=assignment.assigned_by_user_id if assignment else None,
            assignment_status=assignment.status if assignment else None,
            assignment_id=assignment.id if assignment else None,
            accepted_at=assignment.accepted_at if assignment else None,
            rejected_at=assignment.rejected_at if assignment else None,
            assignee_username=assignee_username,
            permissions=TaskPermissionsFlags(**permissions) if permissions else None,
        )


class TaskListItem(BaseModel):
    id: str
    title: str
    status: str
    priority: str
    category: str | None
    tags: list[str]
    due_date: datetime | None
    updated_at: datetime
    goal_id: str | None = None
    subtask_count: int = 0
    completed_subtasks: int = 0
    assigned_to: str | None = None
    assignment_status: str | None = None
    archived_at: datetime | None = None

    model_config = {"from_attributes": True}


class AssignRequest(BaseModel):
    assignee_username: str | None = Field(default=None, max_length=30)
    assignee_user_id: str | None = Field(default=None, max_length=36)
    reason: str | None = Field(default=None, max_length=500)


class RejectRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class AssignmentResponse(BaseModel):
    id: str
    task_id: str
    assignee_user_id: str
    assigned_by_user_id: str
    status: str
    reason: str | None
    assigned_at: datetime
    accepted_at: datetime | None
    rejected_at: datetime | None
    cancelled_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class StatusHistoryResponse(BaseModel):
    id: str
    task_id: str
    from_status: str | None
    to_status: str
    changed_by_user_id: str
    reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityLogResponse(BaseModel):
    id: str
    task_id: str
    actor_user_id: str
    action: str
    field: str | None
    old_value: str | None
    new_value: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WatcherCreate(BaseModel):
    username: str | None = Field(default=None, max_length=30)
    user_id: str | None = Field(default=None, max_length=36)


class WatcherResponse(BaseModel):
    id: str
    task_id: str
    user_id: str
    username: str | None = None
    display_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)


class NoteResponse(BaseModel):
    id: str
    task_id: str
    author_user_id: str
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TagResponse(BaseModel):
    id: str
    name: str

    model_config = {"from_attributes": True}


class TagAttachRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class TaskStatsResponse(BaseModel):
    completed_today: int
    streak_days: int
