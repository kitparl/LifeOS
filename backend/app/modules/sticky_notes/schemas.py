import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

StickyNoteColor = Literal["yellow", "pink", "blue", "green", "purple", "orange", "gray"]

_TAG_MAX_LENGTH = 40
_TAG_MAX_COUNT = 30
_TAG_INVALID_CHARS = re.compile(r"[^a-z0-9_-]")


def normalize_tag(raw: str) -> str:
    """Strip a leading '#', lowercase, trim, and drop disallowed characters."""
    value = raw.strip()
    if value.startswith("#"):
        value = value[1:]
    value = _TAG_INVALID_CHARS.sub("", value.strip().lower())
    return value[:_TAG_MAX_LENGTH]


def normalize_tags(raw: list[str]) -> list[str]:
    """Normalize a list of tags: dedupe, drop empties, cap the count."""
    seen: set[str] = set()
    result: list[str] = []
    for item in raw:
        tag = normalize_tag(item)
        if not tag or tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
    return result[:_TAG_MAX_COUNT]


class StickyNoteCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    color: StickyNoteColor = "yellow"
    is_pinned: bool = False
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def _normalize_tags(cls, v: list[str]) -> list[str]:
        return normalize_tags(v)


class StickyNoteUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    color: StickyNoteColor | None = None
    is_pinned: bool | None = None
    order_index: int | None = None
    tags: list[str] | None = None

    @field_validator("tags")
    @classmethod
    def _normalize_tags(cls, v: list[str] | None) -> list[str] | None:
        return normalize_tags(v) if v is not None else v


class StickyNoteResponse(BaseModel):
    id: str
    title: str | None
    content: str | None
    color: str
    is_pinned: bool
    order_index: int
    note_month: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_validator("tags", mode="before")
    @classmethod
    def _default_tags(cls, v: list[str] | None) -> list[str]:
        return v or []


class StickyNoteMonth(BaseModel):
    month: str
    note_count: int
