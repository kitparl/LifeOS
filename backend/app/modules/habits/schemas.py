from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

HabitFrequency = Literal["daily", "weekly", "monthly"]


class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    frequency: HabitFrequency = "daily"


class HabitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    frequency: HabitFrequency | None = None
    is_active: bool | None = None


class HabitLogResponse(BaseModel):
    id: str
    log_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class HabitStats(BaseModel):
    streak: int
    completion_rate: float
    total_logs: int
    missed_periods: int
    recent_logs: list[HabitLogResponse]


class HabitResponse(BaseModel):
    id: str
    name: str
    description: str | None
    frequency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    completed_today: bool
    streak: int
    completion_rate: float
    stats: HabitStats
    logs: list[HabitLogResponse] = []

    model_config = {"from_attributes": True}


class HabitListItem(BaseModel):
    id: str
    name: str
    frequency: str
    is_active: bool
    completed_today: bool
    streak: int
    completion_rate: float
    updated_at: datetime
