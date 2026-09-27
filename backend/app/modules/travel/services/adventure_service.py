"""Adventures / treks (spec §14, §15): the object, its named waypoints and its route."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, get_or_404
from app.core.pagination import Pagination
from app.modules.travel.geo import decode_polyline
from app.modules.travel.models import TravelAdventure, TravelAdventureWaypoint, TravelRoute, TravelRouteWaypoint
from app.modules.travel.repository.adventures import AdventureRepository
from app.modules.travel.repository.routes import RouteRepository
from app.modules.travel.repository.trips import TripRepository
from app.modules.travel.schemas.adventures import (
    AdventureCreate,
    AdventureDetail,
    AdventureOut,
    AdventureUpdate,
    WaypointOut,
    WaypointsUpdate,
)
from app.modules.travel.schemas.routes import RouteOut

NOT_FOUND = "Adventure not found"


class AdventureService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdventureRepository(db)
        self.trips = TripRepository(db)
        self.routes = RouteRepository(db)

    async def _require(self, user_id: str, adventure_id: str) -> TravelAdventure:
        return get_or_404(await self.repo.get(user_id, adventure_id), NOT_FOUND)

    async def _check_links(self, user_id: str, trip_id: str | None, route_id: str | None) -> None:
        if trip_id and await self.trips.get(user_id, trip_id) is None:
            raise BadRequestError("Unknown trip")
        if route_id and await self.routes.get(user_id, route_id) is None:
            raise BadRequestError("Unknown route")

    async def list_adventures(
        self, user_id: str, trip_id: str | None, pagination: Pagination
    ) -> tuple[list[AdventureOut], int]:
        items, total = await self.repo.list_adventures(user_id, trip_id, pagination)
        return [AdventureOut.model_validate(a) for a in items], total

    async def create(self, user_id: str, data: AdventureCreate) -> AdventureDetail:
        await self._check_links(user_id, data.trip_id, None)
        adventure = await self.repo.add(TravelAdventure(user_id=user_id, **data.model_dump()))
        return await self.detail(user_id, adventure.id)

    async def update(self, user_id: str, adventure_id: str, data: AdventureUpdate) -> AdventureDetail:
        adventure = await self._require(user_id, adventure_id)
        fields = data.model_dump(exclude_unset=True)
        if fields.get("name", "") is None:
            fields.pop("name")
        await self._check_links(user_id, fields.get("trip_id"), fields.get("route_id"))
        for key, value in fields.items():
            setattr(adventure, key, value)
        await self.repo.flush_refresh(adventure)
        return await self.detail(user_id, adventure.id)

    async def delete(self, user_id: str, adventure_id: str) -> None:
        """The adventure's own drawn/imported routes go with it; trip routes are untouched."""
        adventure = await self._require(user_id, adventure_id)
        own = select(TravelRoute.id).where(TravelRoute.adventure_id == adventure.id, TravelRoute.trip_id.is_(None))
        await self.db.execute(delete(TravelRouteWaypoint).where(TravelRouteWaypoint.route_id.in_(own)))
        await self.db.execute(
            delete(TravelRoute).where(TravelRoute.adventure_id == adventure.id, TravelRoute.trip_id.is_(None))
        )
        await self.repo.delete(adventure)

    async def set_waypoints(self, user_id: str, adventure_id: str, data: WaypointsUpdate) -> AdventureDetail:
        adventure = await self._require(user_id, adventure_id)
        await self.repo.replace_waypoints(
            adventure.id,
            [
                TravelAdventureWaypoint(adventure_id=adventure.id, position=i, **w.model_dump())
                for i, w in enumerate(data.waypoints)
            ],
        )
        return await self.detail(user_id, adventure.id)

    async def detail(self, user_id: str, adventure_id: str) -> AdventureDetail:
        adventure = await self._require(user_id, adventure_id)
        route = await self.routes.get(user_id, adventure.route_id) if adventure.route_id else None
        return AdventureDetail(
            adventure=AdventureOut.model_validate(adventure),
            waypoints=[WaypointOut.model_validate(w) for w in await self.repo.waypoints(adventure.id)],
            route=RouteOut.model_validate(route) if route else None,
            route_points=decode_polyline(route.polyline) if route and route.polyline else [],
            elevation_profile=route.elevation_profile if route else None,
        )
