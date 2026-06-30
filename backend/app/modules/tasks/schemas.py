from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TaskStatus = Literal["pending", "in_progress", "completed", "cancelled"]
TaskPriority = Literal["low", "medium", "high", "urgent"]
TaskRecurrence = Literal["none", "daily", "weekly", "monthly"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = "pending"
    priority: TaskPriority = "medium"
    category: str | None = Field(default=None, max_length=64)
    tags: list[str] = Field(default_factory=list)
    due_date: datetime | None = None
    parent_id: str | None = None
    goal_id: str | None = None
    recurrence: TaskRecurrence = "none"


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


class SubtaskResponse(BaseModel):
    id: str
    title: str
    status: str
    priority: str
    completed_at: datetime | None

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, task) -> "TaskResponse":
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
            subtasks=[SubtaskResponse.model_validate(s) for s in task.subtasks],
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
    subtask_count: int = 0
    completed_subtasks: int = 0

    model_config = {"from_attributes": True}
