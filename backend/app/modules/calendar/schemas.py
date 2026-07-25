from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

EventCategory = Literal["personal", "task", "running", "bill", "learning"]
EventRecurrence = Literal["none", "daily", "weekly", "monthly", "yearly"]
EventKind = Literal["normal", "birthday", "immutable"]


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    all_day: bool = False
    category: EventCategory = "personal"
    recurrence: EventRecurrence = "none"
    event_kind: EventKind = "normal"
    location: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def birthday_implies_yearly(self):
        if self.event_kind == "birthday" and self.recurrence != "yearly":
            self.recurrence = "yearly"
        return self


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    all_day: bool | None = None
    category: EventCategory | None = None
    recurrence: EventRecurrence | None = None
    event_kind: EventKind | None = None
    location: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def birthday_implies_yearly(self):
        if self.event_kind == "birthday" and self.recurrence is not None and self.recurrence != "yearly":
            self.recurrence = "yearly"
        elif self.event_kind == "birthday" and self.recurrence is None:
            self.recurrence = "yearly"
        return self


class EventListItem(BaseModel):
    id: str
    title: str
    starts_at: datetime
    ends_at: datetime | None
    all_day: bool
    category: str
    recurrence: str
    event_kind: str = "normal"
    location: str | None
    source_module: str | None = None
    source_id: str | None = None

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
    event_kind: str = "normal"
    location: str | None
    source_module: str | None = None
    source_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
