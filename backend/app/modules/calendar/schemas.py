from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

EventCategory = Literal["personal", "task", "running", "bill", "learning"]
EventRecurrence = Literal["none", "daily", "weekly", "monthly"]


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    all_day: bool = False
    category: EventCategory = "personal"
    recurrence: EventRecurrence = "none"
    location: str | None = Field(default=None, max_length=200)


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    all_day: bool | None = None
    category: EventCategory | None = None
    recurrence: EventRecurrence | None = None
    location: str | None = Field(default=None, max_length=200)


class EventListItem(BaseModel):
    id: str
    title: str
    starts_at: datetime
    ends_at: datetime | None
    all_day: bool
    category: str
    recurrence: str
    location: str | None

    model_config = {"from_attributes": True}


class EventResponse(BaseModel):
    id: str
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime | None
    all_day: bool
    category: str
    recurrence: str
    location: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
