"""Google Maps Platform adapter. Server-side only, and only ever called through `MapsGateway`.

Places (New) and Routes take the key in the `X-Goog-Api-Key` header. The Geocoding and Elevation
web services only accept a `key` query parameter; httpx URL logging is silenced app-wide
(`core/logging_config.py`) and this module never logs URLs, so the key cannot leak to logs.
Field masks keep Places/Routes responses on the cheapest ("Essentials") SKUs.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import httpx

from app.modules.travel.geo import Point, encode_polyline
from app.modules.travel.maps.errors import (
    MapsError,
    MapsInvalidCredential,
    MapsRateLimited,
    MapsTimeout,
    MapsUnavailable,
)
from app.modules.travel.maps.types import GeoResult, RouteResult, Suggestion, TravelMode

TIMEOUT_SECONDS = 10.0
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
ELEVATION_URL = "https://maps.googleapis.com/maps/api/elevation/json"
AUTOCOMPLETE_URL = "https://places.googleapis.com/v1/places:autocomplete"
PLACE_URL = "https://places.googleapis.com/v1/places/"
ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

PLACE_FIELDS = "id,displayName,formattedAddress,location,addressComponents"
ROUTE_FIELDS = "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline"
AUTOCOMPLETE_BIAS_RADIUS_M = 50_000.0

_ROUTE_MODES = {
    TravelMode.DRIVING: "DRIVE",
    TravelMode.WALKING: "WALK",
    TravelMode.CYCLING: "BICYCLE",
    TravelMode.TRANSIT: "TRANSIT",
}
# Most specific first: the name shown for a tapped point.
_NAME_TYPES = (
    "point_of_interest",
    "natural_feature",
    "establishment",
    "park",
    "premise",
    "route",
    "sublocality",
    "locality",
)


def _http_client(timeout: float) -> httpx.AsyncClient:
    """Single construction point for Google HTTP clients (tests patch this seam)."""
    return httpx.AsyncClient(timeout=timeout)


def _latlng(point: Point) -> dict[str, Any]:
    return {"location": {"latLng": {"latitude": point[0], "longitude": point[1]}}}


def _component(components: list[dict[str, Any]], kind: str, *, long_key: str) -> str | None:
    for comp in components:
        if kind in comp.get("types", []):
            return comp.get(long_key)
    return None


def _geocode_to_result(item: dict[str, Any], lat: float, lng: float) -> GeoResult:
    comps = item.get("address_components", [])
    address = item.get("formatted_address")
    name = next(
        (c["long_name"] for t in _NAME_TYPES for c in comps if t in c.get("types", [])),
        None,
    ) or (address.split(",")[0] if address else f"{lat:.5f}, {lng:.5f}")
    return GeoResult(
        name=name,
        address=address,
        country=_component(comps, "country", long_key="long_name"),
        region=_component(comps, "administrative_area_level_1", long_key="long_name"),
        city=_component(comps, "locality", long_key="long_name"),
        # Keep the tapped coordinates: the geocoder's point can be far from where the user tapped.
        lat=lat,
        lng=lng,
        external_place_id=item.get("place_id"),
    )


def _legacy_status_error(status: str) -> MapsError:
    if status == "REQUEST_DENIED":
        return MapsInvalidCredential("Google rejected the API key.")
    if status == "OVER_QUERY_LIMIT":
        return MapsRateLimited("Google quota exceeded.")
    return MapsUnavailable(f"Google returned {status}.")


class GoogleMapsProvider:
    def __init__(self, api_key: str):
        self._key = api_key

    async def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        try:
            async with _http_client(TIMEOUT_SECONDS) as client:
                res = await client.request(method, url, **kwargs)
        except httpx.TimeoutException as exc:
            raise MapsTimeout("Google Maps request timed out.") from exc
        except httpx.HTTPError as exc:
            raise MapsUnavailable("Google Maps is unreachable.") from exc
        if res.status_code in (401, 403):
            raise MapsInvalidCredential("Google rejected the API key.")
        if res.status_code == 429:
            raise MapsRateLimited("Google quota exceeded.")
        if res.status_code >= 400:
            raise MapsUnavailable(f"Google Maps returned HTTP {res.status_code}.")
        try:
            body = res.json()
        except ValueError as exc:
            raise MapsUnavailable("Malformed Google Maps response.") from exc
        if not isinstance(body, dict):
            raise MapsUnavailable("Malformed Google Maps response.")
        return body

    def _new_api_headers(self, field_mask: str) -> dict[str, str]:
        return {"X-Goog-Api-Key": self._key, "X-Goog-FieldMask": field_mask}

    async def reverse_geocode(self, lat: float, lng: float) -> GeoResult | None:
        body = await self._request("GET", GEOCODE_URL, params={"latlng": f"{lat},{lng}", "key": self._key})
        status = body.get("status")
        if status == "ZERO_RESULTS":
            return None
        if status != "OK":
            raise _legacy_status_error(str(status))
        results = body.get("results") or []
        return _geocode_to_result(results[0], lat, lng) if results else None

    async def autocomplete(self, query: str, session_token: str, bias: Point | None) -> list[Suggestion]:
        payload: dict[str, Any] = {"input": query, "sessionToken": session_token}
        if bias is not None:
            payload["locationBias"] = {
                "circle": {
                    "center": {"latitude": bias[0], "longitude": bias[1]},
                    "radius": AUTOCOMPLETE_BIAS_RADIUS_M,
                }
            }
        body = await self._request("POST", AUTOCOMPLETE_URL, json=payload, headers={"X-Goog-Api-Key": self._key})
        out: list[Suggestion] = []
        for item in body.get("suggestions", []):
            pred = item.get("placePrediction")
            if not pred or not pred.get("placeId"):
                continue
            fmt = pred.get("structuredFormat", {})
            out.append(
                Suggestion(
                    external_place_id=pred["placeId"],
                    primary=fmt.get("mainText", {}).get("text") or pred.get("text", {}).get("text", ""),
                    secondary=fmt.get("secondaryText", {}).get("text"),
                )
            )
        return out

    async def place_details(self, external_place_id: str, session_token: str | None) -> GeoResult:
        params = {"sessionToken": session_token} if session_token else None
        body = await self._request(
            "GET", PLACE_URL + external_place_id, params=params, headers=self._new_api_headers(PLACE_FIELDS)
        )
        loc = body.get("location") or {}
        if "latitude" not in loc or "longitude" not in loc:
            raise MapsUnavailable("Malformed Google Maps response.")
        comps = body.get("addressComponents", [])
        return GeoResult(
            name=(body.get("displayName") or {}).get("text") or body.get("formattedAddress") or external_place_id,
            address=body.get("formattedAddress"),
            country=_component(comps, "country", long_key="longText"),
            region=_component(comps, "administrative_area_level_1", long_key="longText"),
            city=_component(comps, "locality", long_key="longText"),
            lat=float(loc["latitude"]),
            lng=float(loc["longitude"]),
            external_place_id=body.get("id") or external_place_id,
        )

    async def compute_route(self, stops: Sequence[Point], mode: TravelMode) -> RouteResult:
        payload: dict[str, Any] = {
            "origin": _latlng(stops[0]),
            "destination": _latlng(stops[-1]),
            "travelMode": _ROUTE_MODES[mode],
        }
        if len(stops) > 2:
            payload["intermediates"] = [_latlng(p) for p in stops[1:-1]]
        body = await self._request("POST", ROUTES_URL, json=payload, headers=self._new_api_headers(ROUTE_FIELDS))
        routes = body.get("routes") or []
        if not routes:
            raise MapsUnavailable("Google found no route for these stops.")
        route = routes[0]
        duration = str(route.get("duration", "")).rstrip("s")
        return RouteResult(
            distance_m=float(route.get("distanceMeters", 0)),
            duration_s=int(float(duration)) if duration else None,
            polyline=(route.get("polyline") or {}).get("encodedPolyline", ""),
        )

    async def elevation(self, path: Sequence[Point], samples: int) -> list[float]:
        body = await self._request(
            "GET",
            ELEVATION_URL,
            params={"path": f"enc:{encode_polyline(path)}", "samples": samples, "key": self._key},
        )
        status = body.get("status")
        if status != "OK":
            raise _legacy_status_error(str(status))
        return [float(r["elevation"]) for r in body.get("results", []) if "elevation" in r]
