"""GPX import (preview -> save) and export (spec §16). The original file is kept in the Files module."""

from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, get_or_404
from app.modules.files.service import FileService
from app.modules.travel.geo import (
    decode_polyline,
    elevation_gain_loss,
    encode_polyline,
    path_length_m,
    simplify_indices,
)
from app.modules.travel.gpx import GpxError, GpxTrack, GpxWaypoint, build_gpx, parse_gpx
from app.modules.travel.models import TravelAdventureWaypoint, TravelRoute
from app.modules.travel.repository.adventures import AdventureRepository
from app.modules.travel.repository.routes import RouteRepository
from app.modules.travel.repository.trips import TripRepository
from app.modules.travel.schemas.adventures import GpxPreview, GpxWaypointOut
from app.modules.travel.schemas.routes import RouteDetail
from app.modules.travel.services.route_service import route_detail

SIMPLIFY_TOLERANCE_M = 5.0
PROFILE_SAMPLES = 200
EXPORTABLE_SOURCES = ("user_drawn", "gpx")
_SAFE_NAME = re.compile(r"[^A-Za-z0-9 _.-]+")


def _parse(data: bytes) -> GpxTrack:
    try:
        return parse_gpx(data)
    except GpxError as exc:
        raise BadRequestError(str(exc)) from exc


def sample_profile(values: list[float], samples: int = PROFILE_SAMPLES) -> list[float]:
    """At most `samples` evenly spaced values, always including the first and last."""
    if len(values) <= samples:
        return [round(v, 1) for v in values]
    step = (len(values) - 1) / (samples - 1)
    return [round(values[round(i * step)], 1) for i in range(samples)]


def _summary(track: GpxTrack) -> tuple[list[tuple[float, float]], float, float | None, float | None]:
    keep = simplify_indices(track.points, SIMPLIFY_TOLERANCE_M)
    simplified = [track.points[i] for i in keep]
    distance = round(path_length_m(track.points), 1)  # measured on the raw track
    if track.has_elevation:
        gain, loss = elevation_gain_loss([e for e in track.elevations if e is not None])
        return simplified, distance, round(gain, 1), round(loss, 1)
    return simplified, distance, None, None


def safe_filename(name: str, suffix: str) -> str:
    stem = _SAFE_NAME.sub("", name).strip()[:80] or "route"
    return f"{stem}{suffix}"


class GpxService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.routes = RouteRepository(db)
        self.trips = TripRepository(db)
        self.adventures = AdventureRepository(db)

    def preview(self, data: bytes) -> GpxPreview:
        track = _parse(data)
        simplified, distance, gain, loss = _summary(track)
        times = [t for t in track.times if t is not None]
        return GpxPreview(
            name=track.name,
            point_count=len(track.points),
            points=simplified,
            distance_m=distance,
            elevation_gain_m=gain,
            elevation_loss_m=loss,
            has_elevation=track.has_elevation,
            has_time=track.has_time,
            start_time=times[0] if times else None,
            end_time=times[-1] if times else None,
            waypoints=[
                GpxWaypointOut(name=w.name, lat=w.lat, lng=w.lng, elevation=w.elevation) for w in track.waypoints
            ],
        )

    async def save(
        self, user_id: str, data: bytes, name: str, trip_id: str | None, adventure_id: str | None
    ) -> RouteDetail:
        """Re-parses the upload (the preview is never trusted), stores the original, and creates a `gpx` route."""
        track = _parse(data)
        if trip_id:
            get_or_404(await self.trips.get(user_id, trip_id), "Trip not found")
        adventure = None
        if adventure_id:
            adventure = get_or_404(await self.adventures.get(user_id, adventure_id), "Adventure not found")
        simplified, distance, gain, loss = _summary(track)
        route = await self.routes.add(
            TravelRoute(
                user_id=user_id,
                trip_id=trip_id,
                adventure_id=adventure_id,
                name=name,
                source="gpx",
                mode="walking",
                distance_m=distance,
                polyline=encode_polyline(simplified),
                elevation_gain_m=gain,
                elevation_loss_m=loss,
                elevation_profile=(
                    sample_profile([e for e in track.elevations if e is not None]) if track.has_elevation else None
                ),
            )
        )
        stored = await FileService(self.db).upload(
            user_id, safe_filename(name, ".gpx.xml"), data, "text/xml", module="travel", entity_id=route.id
        )
        route.gpx_file_id = stored.id
        if adventure is not None:
            adventure.route_id = route.id
            existing = await self.adventures.waypoints(adventure.id)
            await self.adventures.add_waypoints(
                _adventure_waypoints(adventure.id, track.waypoints, start=len(existing))
            )
        return route_detail(await self.routes.flush_refresh(route))

    async def export(self, user_id: str, route_id: str) -> tuple[str, bytes]:
        route = get_or_404(await self.routes.get(user_id, route_id), "Route not found")
        if route.source not in EXPORTABLE_SOURCES:
            # Google-sourced geometry is not ours to redistribute; drawn and imported routes are.
            raise BadRequestError("Only drawn or imported routes can be exported as GPX")
        waypoints = [
            GpxWaypoint(name=w.name or f"Point {w.position + 1}", lat=w.lat, lng=w.lng)
            for w in await self.routes.waypoints(route.id)
        ]
        if route.adventure_id:
            waypoints += [
                GpxWaypoint(name=w.name, lat=w.lat, lng=w.lng, elevation=w.elevation_m)
                for w in await self.adventures.waypoints(route.adventure_id)
            ]
        body = build_gpx(route.name, decode_polyline(route.polyline), waypoints)
        return safe_filename(route.name, ".gpx"), body


def _adventure_waypoints(adventure_id: str, waypoints: list[GpxWaypoint], start: int) -> list[TravelAdventureWaypoint]:
    return [
        TravelAdventureWaypoint(
            adventure_id=adventure_id,
            position=start + i,
            lat=w.lat,
            lng=w.lng,
            name=w.name,
            kind="other",
            elevation_m=w.elevation,
        )
        for i, w in enumerate(waypoints)
    ]
