from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.travel.schemas.common import (
    Lat,
    Links,
    Lng,
    Name,
    Notes,
    OptLinks,
    OptText80,
    OptText120,
    OptText300,
    TagName,
)

PlaceStatus = Literal["wishlist", "planned", "visited", "favourite"]
PlaceCategory = Literal[
    "trek", "mountain", "city", "beach", "nature", "photography", "camping", "road_trip", "adventure", "other"
]
ExternalId = Annotated[str | None, Field(default=None, max_length=255, pattern=r"^[A-Za-z0-9_\-:.]+$")]


class PlaceCreate(BaseModel):
    """Same entity whether it came from search or a map tap (spec §7)."""

    name: Name
    lat: Lat
    lng: Lng
    description: Notes = None
    address: OptText300 = None
    country: OptText80 = None
    region: OptText120 = None
    city: OptText120 = None
    external_place_id: ExternalId = None
    category: PlaceCategory = "other"
    status: PlaceStatus = "wishlist"
    notes: Notes = None
    desired_period: OptText80 = None
    estimated_days: int | None = Field(default=None, ge=1, le=365)
    links: Links
    tags: list[TagName] = Field(default_factory=list, max_length=20)


class PlaceUpdate(BaseModel):
    name: Name | None = None
    lat: Lat | None = None
    lng: Lng | None = None
    description: Notes = None
    address: OptText300 = None
    country: OptText80 = None
    region: OptText120 = None
    city: OptText120 = None
    category: PlaceCategory | None = None
    status: PlaceStatus | None = None
    notes: Notes = None
    desired_period: OptText80 = None
    estimated_days: int | None = Field(default=None, ge=1, le=365)
    links: OptLinks = None


class PlaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    lat: float
    lng: float
    address: str | None
    country: str | None
    region: str | None
    city: str | None
    external_place_id: str | None
    external_source: str | None
    category: str
    status: str
    notes: str | None
    desired_period: str | None
    estimated_days: int | None
    links: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class NearPlaceOut(PlaceOut):
    distance_m: float


class TagsUpdate(BaseModel):
    names: list[TagName] = Field(max_length=20)


MarkerKind = Literal["place", "trip", "adventure", "photo"]


class Marker(BaseModel):
    """Lightweight map marker (T-12): no text blobs, one per saved object with coordinates."""

    id: str
    kind: MarkerKind
    lat: float
    lng: float
    label: str
    status: str | None = None
    trip_id: str | None = None


class ReverseGeocodeIn(BaseModel):
    lat: Lat
    lng: Lng


class GeoOut(BaseModel):
    name: str
    address: str | None
    country: str | None
    region: str | None
    city: str | None
    lat: float
    lng: float
    external_place_id: str | None


class GeoLookupOut(BaseModel):
    """A lookup that may have fallen back: `result` is None and `fallback_reason` says why."""

    result: GeoOut | None
    fallback_reason: str | None = None


class SuggestionOut(BaseModel):
    external_place_id: str
    primary: str
    secondary: str | None


class SuggestionsOut(BaseModel):
    suggestions: list[SuggestionOut]
    fallback_reason: str | None = None


class PlaceHistoryTrip(BaseModel):
    id: str
    name: str
    status: str
    start_date: str | None


class PlaceHistory(BaseModel):
    place: PlaceOut
    trips: list[PlaceHistoryTrip]
    photo_count: int
    recent_photo_ids: list[str]
    journal_count: int
    route_ids: list[str]
