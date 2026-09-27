from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.travel.models import TravelAdventure, TravelRoute, TravelRouteWaypoint


class RouteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: str, route_id: str) -> TravelRoute | None:
        result = await self.db.execute(
            select(TravelRoute).where(TravelRoute.id == route_id, TravelRoute.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def for_trip(self, trip_id: str) -> TravelRoute | None:
        result = await self.db.execute(
            select(TravelRoute).where(TravelRoute.trip_id == trip_id).order_by(TravelRoute.updated_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def add(self, route: TravelRoute) -> TravelRoute:
        self.db.add(route)
        await self.db.flush()
        await self.db.refresh(route)
        return route

    async def flush_refresh(self, route: TravelRoute) -> TravelRoute:
        await self.db.flush()
        await self.db.refresh(route)
        return route

    async def replace_waypoints(self, route_id: str, waypoints: list[TravelRouteWaypoint]) -> None:
        await self.db.execute(delete(TravelRouteWaypoint).where(TravelRouteWaypoint.route_id == route_id))
        self.db.add_all(waypoints)
        await self.db.flush()

    async def waypoints(self, route_id: str) -> list[TravelRouteWaypoint]:
        result = await self.db.execute(
            select(TravelRouteWaypoint)
            .where(TravelRouteWaypoint.route_id == route_id)
            .order_by(TravelRouteWaypoint.position)
        )
        return list(result.scalars().all())

    async def delete(self, route: TravelRoute) -> None:
        await self.db.execute(delete(TravelRouteWaypoint).where(TravelRouteWaypoint.route_id == route.id))
        await self.db.execute(update(TravelAdventure).where(TravelAdventure.route_id == route.id).values(route_id=None))
        await self.db.delete(route)
        await self.db.flush()
