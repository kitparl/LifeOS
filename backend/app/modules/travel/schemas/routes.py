from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.travel.schemas.common import EntityId, Lat, Lng, Name, OptText120

RouteMode = Literal["driving", "walking", "cycling", "transit"]
MAX_DRAWN_POINTS = 5_000

LatLngPair = Annotated[tuple[Lat, Lng], Field(description="[lat, lng]")]


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    source: str
    mode: str
    distance_m: float
    duration_s: int | None
    polyline: str
    elevation_gain_m: float | None
    elevation_loss_m: float | None
    fallback_reason: str | None
    trip_id: str | None
    adventure_id: str | None
    is_stale: bool = False


class RouteRequest(BaseModel):
    mode: RouteMode = "driving"


class DrawnWaypoint(BaseModel):
    lat: Lat
    lng: Lng
    name: OptText120 = None


class RouteDraw(BaseModel):
    """A route the user drew on the map (spec §15); stored as `user_drawn`, never mistaken for Google's."""

    name: Name
    mode: RouteMode = "walking"
    points: list[LatLngPair] = Field(min_length=2, max_length=MAX_DRAWN_POINTS)
    waypoints: list[DrawnWaypoint] = Field(default_factory=list, max_length=100)
    trip_id: EntityId | None = None
    adventure_id: EntityId | None = None


class RouteUpdate(BaseModel):
    name: Name


class RouteDetail(RouteOut):
    model_config = ConfigDict(from_attributes=True)

    points: list[tuple[float, float]]
    elevation_profile: list[float] | None = None
