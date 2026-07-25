from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

RoutineArea = Literal["dsa", "gym", "running", "learning", "communication", "book", "other"]
RoutineCategory = Literal["personal", "task", "running", "bill", "learning"]


class RoutineBlockCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    start_time: time
    end_time: time
    area: RoutineArea = "other"
    category: RoutineCategory = "personal"
    notes: str | None = None
    sort_order: int = 0

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class RoutineBlockUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    start_time: time | None = None
    end_time: time | None = None
    area: RoutineArea | None = None
    category: RoutineCategory | None = None
    notes: str | None = None
    sort_order: int | None = None


class RoutineBlockResponse(BaseModel):
    id: str
    title: str
    start_time: time
    end_time: time
    area: str
    category: str
    notes: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class RoutineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    days_of_week: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])
    timezone: str = Field(default="Asia/Kolkata", max_length=64)
    blocks: list[RoutineBlockCreate] = Field(default_factory=list)

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, v: list[int]) -> list[int]:
        cleaned = sorted({int(d) for d in v if 0 <= int(d) <= 6})
        if not cleaned:
            raise ValueError("days_of_week must include at least one weekday (0=Mon … 6=Sun)")
        return cleaned


class RoutineUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    days_of_week: list[int] | None = None
    timezone: str | None = Field(default=None, max_length=64)
    is_active: bool | None = None
    blocks: list[RoutineBlockCreate] | None = None

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return v
        cleaned = sorted({int(d) for d in v if 0 <= int(d) <= 6})
        if not cleaned:
            raise ValueError("days_of_week must include at least one weekday (0=Mon … 6=Sun)")
        return cleaned


class RoutineListItem(BaseModel):
    id: str
    name: str
    days_of_week: list[int]
    timezone: str
    is_active: bool
    block_count: int
    updated_at: datetime


class RoutineResponse(BaseModel):
    id: str
    name: str
    description: str | None
    days_of_week: list[int]
    timezone: str
    is_active: bool
    blocks: list[RoutineBlockResponse]
    created_at: datetime
    updated_at: datetime
