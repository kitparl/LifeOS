from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.travel.schemas.common import EntityId, Lat, Lng, Name

LocationSource = Literal["exif", "manual"]


class PhotoLinks(BaseModel):
    """Travel objects a photo belongs to (spec §17). Every id is ownership-checked."""

    place_id: EntityId | None = None
    trip_id: EntityId | None = None
    day_id: EntityId | None = None
    adventure_id: EntityId | None = None
    journal_entry_id: EntityId | None = None


class PhotoMeta(PhotoLinks):
    """Sent with the upload. EXIF values arrive only after the user confirmed the suggestion (D-08)."""

    lat: Lat | None = None
    lng: Lng | None = None
    location_source: LocationSource | None = None
    taken_at: datetime | None = None
    caption: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _pair(self) -> PhotoMeta:
        if (self.lat is None) != (self.lng is None):
            raise ValueError("lat and lng go together")
        if self.lat is None:
            self.location_source = None
        elif self.location_source is None:
            self.location_source = "manual"
        return self


class PhotoUpdate(PhotoLinks):
    lat: Lat | None = None
    lng: Lng | None = None
    caption: str | None = Field(default=None, max_length=500)
    taken_at: datetime | None = None


class PhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_id: str
    lat: float | None
    lng: float | None
    location_source: str | None
    taken_at: datetime | None
    caption: str | None
    place_id: str | None
    trip_id: str | None
    day_id: str | None
    adventure_id: str | None
    journal_entry_id: str | None
    created_at: datetime


class JournalCreate(BaseModel):
    entry_date: date
    title: Name
    content: str = Field(default="", max_length=50_000)
    trip_id: EntityId | None = None
    place_id: EntityId | None = None
    adventure_id: EntityId | None = None
    route_id: EntityId | None = None


class JournalUpdate(BaseModel):
    entry_date: date | None = None
    title: Name | None = None
    content: str | None = Field(default=None, max_length=50_000)
    trip_id: EntityId | None = None
    place_id: EntityId | None = None
    adventure_id: EntityId | None = None
    route_id: EntityId | None = None


class JournalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entry_date: date
    title: str
    content: str
    trip_id: str | None
    place_id: str | None
    adventure_id: str | None
    route_id: str | None
    created_at: datetime
    updated_at: datetime
