from datetime import datetime

from pydantic import BaseModel, Field


class WishlistCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: str = Field(default="other", min_length=1, max_length=32)
    cost: float | None = Field(default=None, ge=0)
    progress: int = Field(default=0, ge=0, le=100)
    notes: str | None = None
    image_url: str | None = Field(default=None, max_length=500)


class WishlistUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=32)
    cost: float | None = Field(default=None, ge=0)
    progress: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    image_url: str | None = Field(default=None, max_length=500)


class WishlistCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=32)


class WishlistListItem(BaseModel):
    id: str
    title: str
    category: str
    cost: float | None
    progress: int
    image_url: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class WishlistResponse(BaseModel):
    id: str
    title: str
    description: str | None
    category: str
    cost: float | None
    progress: int
    notes: str | None
    image_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
