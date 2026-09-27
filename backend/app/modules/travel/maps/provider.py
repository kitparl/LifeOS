"""The provider seam. Travel services only ever see `MapsProvider`, reached through `MapsGateway`."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.modules.travel.geo import Point
from app.modules.travel.maps.types import GeoResult, RouteResult, Suggestion, TravelMode


class MapsProvider(Protocol):
    async def reverse_geocode(self, lat: float, lng: float) -> GeoResult | None: ...

    async def autocomplete(self, query: str, session_token: str, bias: Point | None) -> list[Suggestion]: ...

    async def place_details(self, external_place_id: str, session_token: str | None) -> GeoResult: ...

    async def compute_route(self, stops: Sequence[Point], mode: TravelMode) -> RouteResult: ...

    async def elevation(self, path: Sequence[Point], samples: int) -> list[float]: ...
