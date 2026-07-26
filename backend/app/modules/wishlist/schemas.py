from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

WishlistStatus = Literal["in_progress", "completed", "delayed"]
WishlistPriority = Literal["high", "medium", "low"]


def _sync_cover(photos: list[str] | None, image_url: str | None) -> tuple[list[str], str | None]:
    """Prefer photos list; keep image_url as cover (first photo) for list cards."""
    normalized = [str(p) for p in (photos or []) if p]
    if not normalized and image_url:
        normalized = [image_url]
    cover = normalized[0] if normalized else None
    return normalized, cover


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
    photos: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def sync_photos_and_cover(self):
        photos, cover = _sync_cover(self.photos, self.image_url)
        self.photos = photos
        self.image_url = cover
        return self


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
    photos: list[str] | None = None

    @model_validator(mode="after")
    def sync_photos_and_cover(self):
        if self.photos is not None or self.image_url is not None:
            # Only sync when either field is being set (partial updates).
            if self.photos is not None:
                photos, cover = _sync_cover(self.photos, self.image_url)
                self.photos = photos
                self.image_url = cover
            elif self.image_url is not None:
                photos, cover = _sync_cover(None, self.image_url)
                self.photos = photos
                self.image_url = cover
        return self


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
    photos: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def normalize_photos(self):
        photos, cover = _sync_cover(self.photos, self.image_url)
        self.photos = photos
        if not self.image_url:
            self.image_url = cover
        return self
