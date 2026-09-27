"""Routes: Google routing through the gateway with a straight-line fallback, plus user-drawn routes (spec §13, §15).

A trip route is computed only when the user asks (never on map movement). Its `stops_fingerprint`
makes it "stale" as soon as stop order, a stop or the mode changes; the UI then offers Recalculate.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, get_or_404
from app.modules.travel.geo import decode_polyline, elevation_gain_loss, encode_polyline, path_length_m
from app.modules.travel.itinerary import Stop, stops_fingerprint
from app.modules.travel.maps.errors import MapsError
from app.modules.travel.maps.gateway import MapsGateway
from app.modules.travel.maps.types import Feature, RouteResult, Sku, TravelMode
from app.modules.travel.models import TravelRoute, TravelRouteWaypoint
from app.modules.travel.repository.adventures import AdventureRepository
from app.modules.travel.repository.routes import RouteRepository
from app.modules.travel.repository.trips import TripRepository
from app.modules.travel.schemas.routes import RouteDetail, RouteDraw, RouteOut
from app.modules.travel.services.trip_service import TripService

MAX_ELEVATION_SAMPLES = 256  # Elevation API limit per request
ELEVATION_PATH_POINTS = 200  # keeps the encoded path well inside the URL limit
MAX_ROUTE_STOPS = 27  # origin + destination + Google's 25 intermediates
NOT_FOUND = "Route not found"


def straight_line(stops: list[Stop]) -> RouteResult:
    points = [(s.lat, s.lng) for s in stops]
    return RouteResult(distance_m=round(path_length_m(points), 1), duration_s=None, polyline=encode_polyline(points))


class RouteService:
    def __init__(self, db: AsyncSession):
        self.repo = RouteRepository(db)
        self.trips = TripService(db)
        self.trip_repo = TripRepository(db)
        self.adventures = AdventureRepository(db)
        self.gateway = MapsGateway(db)

    async def compute_trip_route(self, user_id: str, trip_id: str, mode: str) -> RouteOut:
        trip, stops = await self.trips.stops(user_id, trip_id)
        if len(stops) < 2:
            raise BadRequestError("Add at least two stops with places to draw a route")
        if len(stops) > MAX_ROUTE_STOPS:
            raise BadRequestError(f"A route can have at most {MAX_ROUTE_STOPS} stops")
        travel_mode = TravelMode(mode)
        points = [(s.lat, s.lng) for s in stops]
        fallback_reason: str | None = None
        if travel_mode is TravelMode.TRANSIT and len(stops) > 2:
            # Google transit routing has no intermediate stops.
            result, fallback_reason = straight_line(stops), "transit_multi_stop"
        else:
            try:
                result = await self.gateway.call(
                    user_id, Sku.ROUTES, Feature.TRIP_ROUTE, lambda p: p.compute_route(points, travel_mode)
                )
            except MapsError as exc:
                result, fallback_reason = straight_line(stops), exc.code

        route = await self.repo.for_trip(trip.id)
        if route is None:
            route = await self.repo.add(
                TravelRoute(user_id=user_id, trip_id=trip.id, name=trip.name, source="straight_line", polyline="")
            )
        route.name = trip.name
        route.source = "straight_line" if fallback_reason else "google"
        route.mode = travel_mode.value
        route.distance_m = result.distance_m
        route.duration_s = result.duration_s
        route.polyline = result.polyline
        route.fallback_reason = fallback_reason
        route.stops_fingerprint = stops_fingerprint(stops, travel_mode.value)
        await self.repo.replace_waypoints(
            route.id,
            [
                TravelRouteWaypoint(
                    route_id=route.id, position=i, lat=s.lat, lng=s.lng, name=s.name, place_id=s.place_id
                )
                for i, s in enumerate(stops)
            ],
        )
        return RouteOut.model_validate(await self.repo.flush_refresh(route))

    async def save_drawn(self, user_id: str, data: RouteDraw) -> RouteDetail:
        if data.trip_id:
            get_or_404(await self.trip_repo.get(user_id, data.trip_id), "Trip not found")
        if data.adventure_id:
            get_or_404(await self.adventures.get(user_id, data.adventure_id), "Adventure not found")
        points = [(lat, lng) for lat, lng in data.points]
        route = await self.repo.add(
            TravelRoute(
                user_id=user_id,
                trip_id=data.trip_id,
                adventure_id=data.adventure_id,
                name=data.name,
                source="user_drawn",
                mode=data.mode,
                distance_m=round(path_length_m(points), 1),
                polyline=encode_polyline(points),
            )
        )
        await self.repo.replace_waypoints(
            route.id,
            [
                TravelRouteWaypoint(route_id=route.id, position=i, lat=w.lat, lng=w.lng, name=w.name)
                for i, w in enumerate(data.waypoints)
            ],
        )
        if data.adventure_id:
            adventure = await self.adventures.get(user_id, data.adventure_id)
            if adventure is not None:
                adventure.route_id = route.id
                await self.repo.flush_refresh(route)
        return route_detail(route)

    async def get(self, user_id: str, route_id: str) -> RouteDetail:
        return route_detail(get_or_404(await self.repo.get(user_id, route_id), NOT_FOUND))

    async def rename(self, user_id: str, route_id: str, name: str) -> RouteDetail:
        route = get_or_404(await self.repo.get(user_id, route_id), NOT_FOUND)
        route.name = name
        return route_detail(await self.repo.flush_refresh(route))

    async def fill_elevation(self, user_id: str, route_id: str) -> RouteDetail:
        """Elevation gain/loss (spec §14). Free when the route came from a GPX with elevation; otherwise one
        tracked Google Elevation request. Without a key it fails with a clear message instead of guessing."""
        route = get_or_404(await self.repo.get(user_id, route_id), NOT_FOUND)
        if route.elevation_profile:
            return route_detail(route)
        points = decode_polyline(route.polyline)
        if len(points) < 2:
            raise BadRequestError("This route has no path to measure")
        path = [points[i] for i in _even_indices(len(points), ELEVATION_PATH_POINTS)]
        samples = min(MAX_ELEVATION_SAMPLES, max(2, len(points)))
        try:
            profile = await self.gateway.call(
                user_id, Sku.ELEVATION, Feature.ADVENTURE_ELEVATION, lambda p: p.elevation(path, samples)
            )
        except MapsError as exc:
            raise BadRequestError(_elevation_unavailable(exc)) from exc
        gain, loss = elevation_gain_loss(profile)
        route.elevation_profile = [round(v, 1) for v in profile]
        route.elevation_gain_m = round(gain, 1)
        route.elevation_loss_m = round(loss, 1)
        return route_detail(await self.repo.flush_refresh(route))

    async def delete(self, user_id: str, route_id: str) -> None:
        await self.repo.delete(get_or_404(await self.repo.get(user_id, route_id), NOT_FOUND))


def route_detail(route: TravelRoute) -> RouteDetail:
    base = RouteOut.model_validate(route).model_dump()
    return RouteDetail(
        **base,
        points=decode_polyline(route.polyline) if route.polyline else [],
        elevation_profile=route.elevation_profile,
    )


def _even_indices(n: int, k: int) -> list[int]:
    if n <= k:
        return list(range(n))
    step = (n - 1) / (k - 1)
    return sorted({round(i * step) for i in range(k)})


def _elevation_unavailable(exc: MapsError) -> str:
    if exc.code == "missing_credential":
        return "Elevation needs a Google Maps key, or import a GPX that already has elevation."
    if exc.code == "cost_protection":
        return "Elevation lookups are paused by maps cost protection."
    return "Elevation is unavailable right now. Try again later."
