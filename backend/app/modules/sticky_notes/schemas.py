from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

StickyNoteColor = Literal["yellow", "pink", "blue", "green", "purple", "orange", "gray"]


class StickyNoteCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    color: StickyNoteColor = "yellow"
    is_pinned: bool = False


class StickyNoteUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    color: StickyNoteColor | None = None
    is_pinned: bool | None = None
    order_index: int | None = None


class StickyNoteResponse(BaseModel):
    id: str
    title: str | None
    content: str | None
    color: str
    is_pinned: bool
    order_index: int
    note_month: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}


class StickyNoteMonth(BaseModel):
    month: str
    note_count: int
