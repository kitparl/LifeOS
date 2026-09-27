from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.travel.schemas.common import EntityId, Lat, Lng, Name, Notes
from app.modules.travel.schemas.routes import RouteOut

AdventureKind = Literal["trek", "hike", "road_trip", "camping", "cycling", "expedition"]
Difficulty = Literal["easy", "moderate", "hard", "expert"]
WaypointKind = Literal["start", "camp", "summit", "water", "viewpoint", "end", "other"]


class AdventureCreate(BaseModel):
    name: Name
    kind: AdventureKind = "trek"
    difficulty: Difficulty | None = None
    trip_id: EntityId | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: Notes = None

    @model_validator(mode="after")
    def _dates(self) -> AdventureCreate:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class AdventureUpdate(BaseModel):
    name: Name | None = None
    kind: AdventureKind | None = None
    difficulty: Difficulty | None = None
    trip_id: EntityId | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: Notes = None
    route_id: EntityId | None = None


class WaypointIn(BaseModel):
    lat: Lat
    lng: Lng
    name: Name
    kind: WaypointKind = "other"
    elevation_m: float | None = Field(default=None, ge=-500, le=9000)


class WaypointsUpdate(BaseModel):
    waypoints: list[WaypointIn] = Field(max_length=200)


class WaypointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    position: int
    lat: float
    lng: float
    name: str
    kind: str
    elevation_m: float | None


class AdventureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    kind: str
    difficulty: str | None
    trip_id: str | None
    start_date: date | None
    end_date: date | None
    route_id: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AdventureDetail(BaseModel):
    adventure: AdventureOut
    waypoints: list[WaypointOut]
    route: RouteOut | None
    route_points: list[tuple[float, float]]
    elevation_profile: list[float] | None


class GpxWaypointOut(BaseModel):
    name: str
    lat: float
    lng: float
    elevation: float | None


class GpxPreview(BaseModel):
    """Stateless preview; nothing is stored until the user saves (spec §16 workflow)."""

    name: str | None
    point_count: int
    points: list[tuple[float, float]]
    distance_m: float
    elevation_gain_m: float | None
    elevation_loss_m: float | None
    has_elevation: bool
    has_time: bool
    start_time: datetime | None
    end_time: datetime | None
    waypoints: list[GpxWaypointOut]
