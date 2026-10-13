"""The plan document shared on a trip link: days of stops, stored as one validated JSON value.

Limits reuse the trip ones (days, stops, text lengths) so an applied plan always fits the real
itinerary tables (requirements T-08).
"""

from __future__ import annotations

from datetime import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.travel.schemas.common import EntityId, Lat, Links, Lng, Name, Notes, OptText120, OptText200
from app.modules.travel.schemas.places import ExternalId
from app.modules.travel.schemas.trips import MAX_ORDER_ITEMS, MAX_TRIP_DAYS

StopKind = Literal["stay", "food", "travel", "sightseeing", "rest", "other"]
# Serialized size cap for one document (and the request body that carries it).
MAX_PLAN_BYTES = 512 * 1024


class PlanPlace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name
    lat: Lat
    lng: Lng
    google_place_id: ExternalId = None


class PlanStop(BaseModel):
    """`id` is stable across copies, so a plan can be compared with the Original it started from."""

    model_config = ConfigDict(extra="forbid")

    id: EntityId
    title: Name
    kind: StopKind = "other"
    place: PlanPlace | None = None
    start_time: time | None = None
    end_time: time | None = None
    transport: OptText120 = None
    stay: OptText200 = None
    notes: Notes = None
    links: Links


class PlanDay(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: OptText200 = None
    notes: Notes = None
    stops: list[PlanStop] = Field(default_factory=list, max_length=MAX_ORDER_ITEMS)


class PlanDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    days: list[PlanDay] = Field(default_factory=list, max_length=MAX_TRIP_DAYS)

    @model_validator(mode="after")
    def _limits(self) -> PlanDocument:
        ids = [stop.id for day in self.days for stop in day.stops]
        if len(ids) > MAX_ORDER_ITEMS:
            raise ValueError(f"a plan can have at most {MAX_ORDER_ITEMS} stops")
        if len(set(ids)) != len(ids):
            raise ValueError("stop ids must be unique")
        return self

    def stops(self) -> list[PlanStop]:
        return [stop for day in self.days for stop in day.stops]
