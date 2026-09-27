"""My World: one lightweight payload for every map layer (spec §5 layers, §20; requirements T-12).

Markers carry no text blobs; details load only when a marker is opened.
"""

from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.travel.geo import decode_polyline
from app.modules.travel.models import (
    TravelAdventure,
    TravelAdventureWaypoint,
    TravelPlace,
    TravelRoute,
    TravelTrip,
    TravelTripPlace,
)
from app.modules.travel.repository.memories import MemoryRepository
from app.modules.travel.schemas.places import Marker
from app.modules.travel.schemas.world import WorldCounts, WorldOverview
from app.modules.travel.services.place_service import PlaceService


class WorldService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.places = PlaceService(db)
        self.memories = MemoryRepository(db)

    async def markers(self, user_id: str) -> list[Marker]:
        return [
            *await self.places.markers(user_id),
            *await self._trip_markers(user_id),
            *await self._adventure_markers(user_id),
            *[
                Marker(id=pid, kind="photo", lat=lat, lng=lng, label=caption or "Photo", trip_id=trip_id)
                for pid, lat, lng, caption, trip_id in await self.memories.photo_markers(user_id)
            ],
        ]

    async def overview(self, user_id: str) -> WorldOverview:
        markers = await self.markers(user_id)
        statuses = Counter(m.status for m in markers if m.kind == "place")
        trip_statuses = Counter(
            (await self.db.execute(select(TravelTrip.status).where(TravelTrip.user_id == user_id))).scalars().all()
        )
        adventures = len(
            (await self.db.execute(select(TravelAdventure.id).where(TravelAdventure.user_id == user_id))).all()
        )
        return WorldOverview(
            markers=markers,
            counts=WorldCounts(
                wishlist=statuses["wishlist"],
                planned=statuses["planned"],
                visited=statuses["visited"],
                favourite=statuses["favourite"],
                trips=sum(trip_statuses.values()),
                completed_trips=trip_statuses["completed"],
                adventures=adventures,
                photos=sum(1 for m in markers if m.kind == "photo"),
            ),
        )

    async def _trip_markers(self, user_id: str) -> list[Marker]:
        """One marker per trip, at its first saved place."""
        result = await self.db.execute(
            select(TravelTrip.id, TravelTrip.name, TravelTrip.status, TravelPlace.lat, TravelPlace.lng)
            .join(TravelTripPlace, TravelTripPlace.trip_id == TravelTrip.id)
            .join(TravelPlace, TravelPlace.id == TravelTripPlace.place_id)
            .where(TravelTrip.user_id == user_id)
            .order_by(TravelTrip.id, TravelTripPlace.created_at)
        )
        seen: set[str] = set()
        out: list[Marker] = []
        for trip_id, name, status, lat, lng in result.all():
            if trip_id in seen:
                continue
            seen.add(trip_id)
            out.append(Marker(id=trip_id, kind="trip", lat=lat, lng=lng, label=name, status=status, trip_id=trip_id))
        return out

    async def _adventure_markers(self, user_id: str) -> list[Marker]:
        """At the route start, else the first waypoint; adventures with neither have nowhere to be shown."""
        adventures = (
            await self.db.execute(
                select(TravelAdventure.id, TravelAdventure.name, TravelAdventure.trip_id, TravelRoute.polyline)
                .outerjoin(TravelRoute, TravelRoute.id == TravelAdventure.route_id)
                .where(TravelAdventure.user_id == user_id)
            )
        ).all()
        firsts = {
            adv_id: (lat, lng)
            for adv_id, lat, lng in (
                await self.db.execute(
                    select(
                        TravelAdventureWaypoint.adventure_id, TravelAdventureWaypoint.lat, TravelAdventureWaypoint.lng
                    )
                    .where(TravelAdventureWaypoint.adventure_id.in_([a[0] for a in adventures]))
                    .where(TravelAdventureWaypoint.position == 0)
                )
            ).all()
        }
        out: list[Marker] = []
        for adv_id, name, trip_id, polyline in adventures:
            start = decode_polyline(polyline, limit=1) if polyline else []
            point = start[0] if start else firsts.get(adv_id)
            if point:
                out.append(Marker(id=adv_id, kind="adventure", lat=point[0], lng=point[1], label=name, trip_id=trip_id))
        return out
