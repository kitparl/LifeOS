from datetime import date, datetime

from pydantic import BaseModel, Field


class MilestoneCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    milestone_date: date
    photo_file_ids: str | None = None
    tags: str | None = None
    ai_generated: bool = False


class MilestoneUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    milestone_date: date | None = None
    photo_file_ids: str | None = None
    tags: str | None = None


class MilestoneResponse(BaseModel):
    id: str
    title: str
    description: str | None
    milestone_date: date
    photo_file_ids: str | None
    tags: str | None
    ai_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LifeTimelineItem(BaseModel):
    item_type: str
    module: str
    id: str
    title: str
    description: str | None = None
    occurred_at: datetime
    route: str | None = None
    photo_file_ids: str | None = None
    ai_generated: bool = False
    tags: str | None = None
