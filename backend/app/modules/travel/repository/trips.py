from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.modules.travel.models import (
    TravelAdventure,
    TravelItineraryDay,
    TravelItineraryItem,
    TravelJournalEntry,
    TravelPhoto,
    TravelPlace,
    TravelRoute,
    TravelRouteWaypoint,
    TravelTrip,
    TravelTripPlace,
)


class TripRepository:
    """Trip aggregate: trip, its places, days and items. Callers pass an already-owned trip."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- trips ------------------------------------------------------------------------------

    async def list_trips(
        self, user_id: str, status: str | None, pagination: Pagination
    ) -> tuple[list[TravelTrip], int]:
        stmt = select(TravelTrip).where(TravelTrip.user_id == user_id)
        if status:
            stmt = stmt.where(TravelTrip.status == status)
        stmt = stmt.order_by(TravelTrip.start_date.desc().nulls_first(), TravelTrip.updated_at.desc())
        return await paginate(self.db, stmt, pagination)

    async def place_counts(self, trip_ids: list[str]) -> dict[str, int]:
        if not trip_ids:
            return {}
        result = await self.db.execute(
            select(TravelTripPlace.trip_id, func.count())
            .where(TravelTripPlace.trip_id.in_(trip_ids))
            .group_by(TravelTripPlace.trip_id)
        )
        return {trip_id: int(n) for trip_id, n in result.all()}

    async def get(self, user_id: str, trip_id: str) -> TravelTrip | None:
        result = await self.db.execute(
            select(TravelTrip).where(TravelTrip.id == trip_id, TravelTrip.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add(self, trip: TravelTrip) -> TravelTrip:
        self.db.add(trip)
        await self.db.flush()
        await self.db.refresh(trip)
        return trip

    async def flush(self) -> None:
        await self.db.flush()

    async def delete(self, trip: TravelTrip) -> None:
        """Planning rows go; memories stay (photos/journal/adventures are unlinked, spec §21)."""
        route_ids = select(TravelRoute.id).where(TravelRoute.trip_id == trip.id)
        await self.db.execute(delete(TravelRouteWaypoint).where(TravelRouteWaypoint.route_id.in_(route_ids)))
        await self.db.execute(delete(TravelRoute).where(TravelRoute.trip_id == trip.id))
        await self.db.execute(delete(TravelItineraryItem).where(TravelItineraryItem.trip_id == trip.id))
        await self.db.execute(delete(TravelItineraryDay).where(TravelItineraryDay.trip_id == trip.id))
        await self.db.execute(delete(TravelTripPlace).where(TravelTripPlace.trip_id == trip.id))
        await self.db.execute(
            update(TravelPhoto).where(TravelPhoto.trip_id == trip.id).values(trip_id=None, day_id=None)
        )
        await self.db.execute(
            update(TravelJournalEntry).where(TravelJournalEntry.trip_id == trip.id).values(trip_id=None)
        )
        await self.db.execute(update(TravelAdventure).where(TravelAdventure.trip_id == trip.id).values(trip_id=None))
        await self.db.delete(trip)
        await self.db.flush()

    # ---- places in a trip ---------------------------------------------------------------------

    async def trip_places(self, trip_id: str) -> list[tuple[TravelTripPlace, TravelPlace]]:
        result = await self.db.execute(
            select(TravelTripPlace, TravelPlace)
            .join(TravelPlace, TravelPlace.id == TravelTripPlace.place_id)
            .where(TravelTripPlace.trip_id == trip_id)
            .order_by(TravelTripPlace.created_at)
        )
        return [(link, place) for link, place in result.all()]

    async def get_link(self, trip_id: str, place_id: str) -> TravelTripPlace | None:
        result = await self.db.execute(
            select(TravelTripPlace).where(TravelTripPlace.trip_id == trip_id, TravelTripPlace.place_id == place_id)
        )
        return result.scalar_one_or_none()

    async def add_link(self, trip_id: str, place_id: str) -> TravelTripPlace:
        link = await self.get_link(trip_id, place_id)
        if link is None:
            link = TravelTripPlace(trip_id=trip_id, place_id=place_id)
            self.db.add(link)
            await self.db.flush()
        return link

    async def remove_link(self, trip_id: str, place_id: str) -> None:
        await self.db.execute(
            delete(TravelItineraryItem).where(
                TravelItineraryItem.trip_id == trip_id, TravelItineraryItem.place_id == place_id
            )
        )
        await self.db.execute(
            delete(TravelTripPlace).where(TravelTripPlace.trip_id == trip_id, TravelTripPlace.place_id == place_id)
        )
        await self.db.flush()

    # ---- days and items -----------------------------------------------------------------------

    async def days(self, trip_id: str) -> list[TravelItineraryDay]:
        result = await self.db.execute(
            select(TravelItineraryDay)
            .where(TravelItineraryDay.trip_id == trip_id)
            .order_by(TravelItineraryDay.day_index)
        )
        return list(result.scalars().all())

    async def get_day(self, trip_id: str, day_id: str) -> TravelItineraryDay | None:
        result = await self.db.execute(
            select(TravelItineraryDay).where(TravelItineraryDay.id == day_id, TravelItineraryDay.trip_id == trip_id)
        )
        return result.scalar_one_or_none()

    async def add_days(self, days: list[TravelItineraryDay]) -> None:
        self.db.add_all(days)
        await self.db.flush()

    async def delete_day(self, day: TravelItineraryDay) -> None:
        await self.db.execute(delete(TravelItineraryItem).where(TravelItineraryItem.day_id == day.id))
        await self.db.delete(day)
        await self.db.flush()

    async def items(self, trip_id: str) -> list[TravelItineraryItem]:
        result = await self.db.execute(
            select(TravelItineraryItem)
            .where(TravelItineraryItem.trip_id == trip_id)
            .order_by(TravelItineraryItem.position)
        )
        return list(result.scalars().all())

    async def get_item(self, trip_id: str, item_id: str) -> TravelItineraryItem | None:
        result = await self.db.execute(
            select(TravelItineraryItem).where(TravelItineraryItem.id == item_id, TravelItineraryItem.trip_id == trip_id)
        )
        return result.scalar_one_or_none()

    async def next_position(self, day_id: str) -> int:
        top = await self.db.scalar(
            select(func.max(TravelItineraryItem.position)).where(TravelItineraryItem.day_id == day_id)
        )
        return 0 if top is None else int(top) + 1

    async def add_item(self, item: TravelItineraryItem) -> TravelItineraryItem:
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete_item(self, item: TravelItineraryItem) -> None:
        await self.db.delete(item)
        await self.db.flush()
