from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

JournalType = Literal["morning", "night", "reflection", "gratitude"]


class JournalCreate(BaseModel):
    entry_date: date
    entry_type: JournalType = "morning"
    title: str | None = Field(default=None, max_length=200)
    content: str = ""
    gratitude: str | None = None
    wins: str | None = None
    lessons: str | None = None


class JournalUpdate(BaseModel):
    entry_date: date | None = None
    entry_type: JournalType | None = None
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    gratitude: str | None = None
    wins: str | None = None
    lessons: str | None = None


class JournalListItem(BaseModel):
    id: str
    entry_date: date
    entry_type: str
    title: str | None
    content: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class JournalResponse(BaseModel):
    id: str
    entry_date: date
    entry_type: str
    title: str | None
    content: str
    gratitude: str | None
    wins: str | None
    lessons: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
