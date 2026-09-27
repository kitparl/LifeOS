"""Provider-neutral value types returned by every `MapsProvider`."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Sku(str, Enum):  # not StrEnum: the backend must run on Python 3.10
    """Billable operations. Values are the keys of `map_pricing_configurations.sku`."""

    GEOCODING = "geocoding"
    PLACES_AUTOCOMPLETE = "places_autocomplete"
    PLACE_DETAILS = "place_details"
    ROUTES = "routes"
    ELEVATION = "elevation"


# Reverse geocode on a map tap keeps working after the safety budget while its own free allowance lasts.
ESSENTIAL_SKUS: frozenset[Sku] = frozenset({Sku.GEOCODING})

SKU_API: dict[Sku, str] = {
    Sku.GEOCODING: "geocoding",
    Sku.PLACES_AUTOCOMPLETE: "places",
    Sku.PLACE_DETAILS: "places",
    Sku.ROUTES: "routes",
    Sku.ELEVATION: "elevation",
}


class Feature(str, Enum):
    """Which part of Travel generated a request (usage reporting)."""

    MAP_TAP = "map_tap"
    SEARCH = "search"
    SEARCH_SELECT = "search_select"
    TRIP_ROUTE = "trip_route"
    ADVENTURE_ELEVATION = "adventure_elevation"
    CONNECTION_TEST = "connection_test"


class TravelMode(str, Enum):
    DRIVING = "driving"
    WALKING = "walking"
    CYCLING = "cycling"
    TRANSIT = "transit"


@dataclass(frozen=True)
class GeoResult:
    name: str
    address: str | None
    country: str | None
    region: str | None
    city: str | None
    lat: float
    lng: float
    external_place_id: str | None


@dataclass(frozen=True)
class Suggestion:
    external_place_id: str
    primary: str
    secondary: str | None


@dataclass(frozen=True)
class RouteResult:
    distance_m: float
    duration_s: int | None
    polyline: str
