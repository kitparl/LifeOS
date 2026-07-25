from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

GoalStatus = Literal["active", "archived", "completed"]
GoalPeriod = Literal["weekly", "monthly", "yearly", "custom"]


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


class GoalCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=32)


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: str = Field(default="personal", min_length=1, max_length=32)
    period: GoalPeriod = "yearly"
    progress: int = Field(default=0, ge=0, le=100)
    notes: str | None = None
    target_date: datetime | None = None
    period_start: date | None = None
    period_end: date | None = None
    parent_id: str | None = None


class GoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=32)
    status: GoalStatus | None = None
    period: GoalPeriod | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    target_date: datetime | None = None
    period_start: date | None = None
    period_end: date | None = None


class GoalResponse(BaseModel):
    id: str
    title: str
    description: str | None
    category: str
    status: str
    period: str
    progress: int
    notes: str | None
    target_date: datetime | None
    period_start: date | None
    period_end: date | None
    parent_id: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    milestones: list[MilestoneResponse] = []
    is_missed: bool = False

    model_config = {"from_attributes": True}


class GoalListItem(BaseModel):
    id: str
    title: str
    category: str
    status: str
    period: str
    progress: int
    target_date: datetime | None
    period_start: date | None = None
    period_end: date | None = None
    updated_at: datetime
    milestone_count: int = 0
    completed_milestones: int = 0
    is_missed: bool = False

    model_config = {"from_attributes": True}
