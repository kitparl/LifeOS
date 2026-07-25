from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

WishlistStatus = Literal["in_progress", "completed", "delayed"]
WishlistPriority = Literal["high", "medium", "low"]


class WishlistCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: str = Field(default="other", min_length=1, max_length=32)
    target_year: int | None = Field(default=None, ge=1900, le=2200)
    achieved_date: date | None = None
    status: WishlistStatus = "in_progress"
    priority: WishlistPriority = "medium"
    notes: str | None = None
    image_url: str | None = Field(default=None, max_length=500)


class WishlistUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=32)
    target_year: int | None = Field(default=None, ge=1900, le=2200)
    achieved_date: date | None = None
    status: WishlistStatus | None = None
    priority: WishlistPriority | None = None
    notes: str | None = None
    image_url: str | None = Field(default=None, max_length=500)


class WishlistCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=32)


class WishlistListItem(BaseModel):
    id: str
    title: str
    category: str
    target_year: int | None
    achieved_date: date | None
    status: str
    priority: str
    image_url: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class WishlistResponse(BaseModel):
    id: str
    title: str
    description: str | None
    category: str
    target_year: int | None
    achieved_date: date | None
    status: str
    priority: str
    notes: str | None
    image_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
