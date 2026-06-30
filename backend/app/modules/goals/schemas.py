from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

GoalCategory = Literal["career", "running", "finance", "learning", "personal", "health"]
GoalStatus = Literal["active", "archived", "completed"]


class MilestoneCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class MilestoneUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    completed: bool | None = None


class MilestoneResponse(BaseModel):
    id: str
    title: str
    completed: bool
    sort_order: int
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: GoalCategory = "personal"
    progress: int = Field(default=0, ge=0, le=100)
    notes: str | None = None
    target_date: datetime | None = None
    parent_id: str | None = None


class GoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category: GoalCategory | None = None
    status: GoalStatus | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    target_date: datetime | None = None


class GoalResponse(BaseModel):
    id: str
    title: str
    description: str | None
    category: str
    status: str
    progress: int
    notes: str | None
    target_date: datetime | None
    parent_id: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    milestones: list[MilestoneResponse] = []

    model_config = {"from_attributes": True}


class GoalListItem(BaseModel):
    id: str
    title: str
    category: str
    status: str
    progress: int
    target_date: datetime | None
    updated_at: datetime
    milestone_count: int = 0
    completed_milestones: int = 0

    model_config = {"from_attributes": True}
