from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.modules.travel.models import TravelAdventure, TravelAdventureWaypoint


class AdventureRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_adventures(
        self, user_id: str, trip_id: str | None, pagination: Pagination
    ) -> tuple[list[TravelAdventure], int]:
        stmt = select(TravelAdventure).where(TravelAdventure.user_id == user_id)
        if trip_id:
            stmt = stmt.where(TravelAdventure.trip_id == trip_id)
        stmt = stmt.order_by(TravelAdventure.start_date.desc().nulls_first(), TravelAdventure.updated_at.desc())
        return await paginate(self.db, stmt, pagination)

    async def get(self, user_id: str, adventure_id: str) -> TravelAdventure | None:
        result = await self.db.execute(
            select(TravelAdventure).where(TravelAdventure.id == adventure_id, TravelAdventure.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add(self, adventure: TravelAdventure) -> TravelAdventure:
        self.db.add(adventure)
        await self.db.flush()
        await self.db.refresh(adventure)
        return adventure

    async def flush_refresh(self, adventure: TravelAdventure) -> TravelAdventure:
        await self.db.flush()
        await self.db.refresh(adventure)
        return adventure

    async def delete(self, adventure: TravelAdventure) -> None:
        await self.db.execute(
            delete(TravelAdventureWaypoint).where(TravelAdventureWaypoint.adventure_id == adventure.id)
        )
        await self.db.delete(adventure)
        await self.db.flush()

    async def waypoints(self, adventure_id: str) -> list[TravelAdventureWaypoint]:
        result = await self.db.execute(
            select(TravelAdventureWaypoint)
            .where(TravelAdventureWaypoint.adventure_id == adventure_id)
            .order_by(TravelAdventureWaypoint.position)
        )
        return list(result.scalars().all())

    async def replace_waypoints(self, adventure_id: str, waypoints: list[TravelAdventureWaypoint]) -> None:
        await self.db.execute(
            delete(TravelAdventureWaypoint).where(TravelAdventureWaypoint.adventure_id == adventure_id)
        )
        self.db.add_all(waypoints)
        await self.db.flush()

    async def add_waypoints(self, waypoints: list[TravelAdventureWaypoint]) -> None:
        self.db.add_all(waypoints)
        await self.db.flush()
