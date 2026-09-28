from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.travel.schemas.common import EntityId, Links, Name, Notes, OptLinks, OptText120, OptText200
from app.modules.travel.schemas.routes import RouteOut

TripStatus = Literal["draft", "planning", "booked", "active", "completed"]
MAX_TRIP_DAYS = 120
MAX_ORDER_ITEMS = 500


def check_trip_dates(start: date | None, end: date | None) -> None:
    if start and end:
        if end < start:
            raise ValueError("end_date must be on or after start_date")
        if (end - start).days + 1 > MAX_TRIP_DAYS:
            raise ValueError(f"a trip can span at most {MAX_TRIP_DAYS} days")


class TripCreate(BaseModel):
    """A new trip is always a draft (requirements D-12); dates may be missing or tentative."""

    name: Name
    description: Notes = None
    start_date: date | None = None
    end_date: date | None = None
    dates_tentative: bool = True
    notes: Notes = None

    @model_validator(mode="after")
    def _dates(self) -> TripCreate:
        check_trip_dates(self.start_date, self.end_date)
        return self


class TripUpdate(BaseModel):
    """Autosave-friendly PATCH; status changes go through the lifecycle endpoints."""

    name: Name | None = None
    description: Notes = None
    start_date: date | None = None
    end_date: date | None = None
    dates_tentative: bool | None = None
    notes: Notes = None
    cover_photo_id: EntityId | None = None


class TripStatusChange(BaseModel):
    status: Literal["planning", "booked", "active"]


class TripSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    start_date: date | None
    end_date: date | None
    dates_tentative: bool
    status: TripStatus
    cover_photo_id: str | None
    notes: str | None
    confirmed_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TripListItem(TripSummary):
    place_count: int = 0


class DayCreate(BaseModel):
    title: OptText200 = None
    notes: Notes = None


class DayUpdate(BaseModel):
    title: OptText200 = None
    notes: Notes = None


class ItemCreate(BaseModel):
    day_id: EntityId
    title: Name
    place_id: EntityId | None = None
    start_time: time | None = None
    end_time: time | None = None
    transport: OptText120 = None
    accommodation: OptText200 = None
    notes: Notes = None
    links: Links


class ItemUpdate(BaseModel):
    title: Name | None = None
    place_id: EntityId | None = None
    start_time: time | None = None
    end_time: time | None = None
    transport: OptText120 = None
    accommodation: OptText200 = None
    notes: Notes = None
    links: OptLinks = None


class ItineraryOrder(BaseModel):
    """The whole layout after a drag: every day's item ids in order (one request per drag)."""

    days: dict[EntityId, list[EntityId]] = Field(max_length=MAX_TRIP_DAYS)

    @model_validator(mode="after")
    def _size(self) -> ItineraryOrder:
        if sum(len(v) for v in self.days.values()) > MAX_ORDER_ITEMS:
            raise ValueError("too many items")
        return self


class TripPlaceAdd(BaseModel):
    day_id: EntityId | None = None


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    day_id: str
    position: int
    place_id: str | None
    title: str
    start_time: time | None
    end_time: time | None
    transport: str | None
    accommodation: str | None
    notes: str | None
    links: list[str] = Field(default_factory=list)


class DayOut(BaseModel):
    id: str
    day_index: int
    day_date: date | None
    title: str | None
    notes: str | None
    items: list[ItemOut]


class TripPlaceOut(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    status: str
    external_place_id: str | None


class StopOut(BaseModel):
    place_id: str
    day_id: str
    name: str
    lat: float
    lng: float


class TripDetail(BaseModel):
    trip: TripSummary
    days: list[DayOut]
    places: list[TripPlaceOut]
    stops: list[StopOut]
    route: RouteOut | None
