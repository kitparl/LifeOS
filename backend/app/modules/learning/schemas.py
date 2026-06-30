from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class LearningCreate(BaseModel):
    item_type: str = "book"
    title: str = Field(min_length=1, max_length=200)
    provider: str | None = None
    url: str | None = None
    status: str = "planned"
    progress: int = Field(default=0, ge=0, le=100)
    target_date: date | None = None
    notes: str | None = None


class LearningUpdate(BaseModel):
    item_type: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    provider: str | None = None
    url: str | None = None
    status: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    target_date: date | None = None
    notes: str | None = None


class LearningListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_type: str
    title: str
    provider: str | None
    status: str
    progress: int
    target_date: date | None
    updated_at: datetime


class LearningResponse(LearningListItem):
    url: str | None
    notes: str | None
    created_at: datetime
