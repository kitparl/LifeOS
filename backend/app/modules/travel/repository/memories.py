from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.modules.travel.models import (
    TravelAdventure,
    TravelItineraryDay,
    TravelJournalEntry,
    TravelPhoto,
    TravelPlace,
    TravelRoute,
    TravelTrip,
)


class MemoryRepository:
    """Photos and travel journal entries (spec §17–§19)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- ownership of linked objects --------------------------------------------------------------

    async def owns(self, user_id: str, model: type, object_id: str) -> bool:
        found = await self.db.scalar(
            select(func.count()).select_from(model).where(model.id == object_id, model.user_id == user_id)
        )
        return bool(found)

    async def owns_day(self, user_id: str, day_id: str) -> bool:
        found = await self.db.scalar(
            select(func.count())
            .select_from(TravelItineraryDay)
            .join(TravelTrip, TravelTrip.id == TravelItineraryDay.trip_id)
            .where(TravelItineraryDay.id == day_id, TravelTrip.user_id == user_id)
        )
        return bool(found)

    # ---- photos ------------------------------------------------------------------------------

    async def list_photos(
        self, user_id: str, filters: dict[str, str | None], has_location: bool | None, pagination: Pagination
    ) -> tuple[list[TravelPhoto], int]:
        stmt = select(TravelPhoto).where(TravelPhoto.user_id == user_id)
        for column, value in filters.items():
            if value:
                stmt = stmt.where(getattr(TravelPhoto, column) == value)
        if has_location is True:
            stmt = stmt.where(TravelPhoto.lat.is_not(None))
        elif has_location is False:
            stmt = stmt.where(TravelPhoto.lat.is_(None))
        stmt = stmt.order_by(TravelPhoto.taken_at.desc().nulls_last(), TravelPhoto.created_at.desc())
        return await paginate(self.db, stmt, pagination)

    async def get_photo(self, user_id: str, photo_id: str) -> TravelPhoto | None:
        result = await self.db.execute(
            select(TravelPhoto).where(TravelPhoto.id == photo_id, TravelPhoto.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add(self, row: TravelPhoto | TravelJournalEntry) -> None:
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)

    async def flush_refresh(self, row: TravelPhoto | TravelJournalEntry) -> None:
        await self.db.flush()
        await self.db.refresh(row)

    async def delete(self, row: TravelPhoto | TravelJournalEntry) -> None:
        await self.db.delete(row)
        await self.db.flush()

    async def photo_markers(self, user_id: str) -> list[tuple[str, float, float, str | None, str | None]]:
        result = await self.db.execute(
            select(TravelPhoto.id, TravelPhoto.lat, TravelPhoto.lng, TravelPhoto.caption, TravelPhoto.trip_id).where(
                TravelPhoto.user_id == user_id, TravelPhoto.lat.is_not(None)
            )
        )
        return [tuple(row) for row in result.all()]

    # ---- journal -----------------------------------------------------------------------------

    async def list_journal(
        self, user_id: str, trip_id: str | None, place_id: str | None, pagination: Pagination
    ) -> tuple[list[TravelJournalEntry], int]:
        stmt = select(TravelJournalEntry).where(TravelJournalEntry.user_id == user_id)
        if trip_id:
            stmt = stmt.where(TravelJournalEntry.trip_id == trip_id)
        if place_id:
            stmt = stmt.where(TravelJournalEntry.place_id == place_id)
        stmt = stmt.order_by(TravelJournalEntry.entry_date.desc(), TravelJournalEntry.created_at.desc())
        return await paginate(self.db, stmt, pagination)

    async def get_entry(self, user_id: str, entry_id: str) -> TravelJournalEntry | None:
        result = await self.db.execute(
            select(TravelJournalEntry).where(TravelJournalEntry.id == entry_id, TravelJournalEntry.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def unlink_entry_photos(self, entry_id: str) -> None:
        await self.db.execute(
            update(TravelPhoto).where(TravelPhoto.journal_entry_id == entry_id).values(journal_entry_id=None)
        )


# Link column -> owning model, used to verify every linked id belongs to the caller (IDOR).
LINK_MODELS: dict[str, type] = {
    "place_id": TravelPlace,
    "trip_id": TravelTrip,
    "adventure_id": TravelAdventure,
    "journal_entry_id": TravelJournalEntry,
    "route_id": TravelRoute,
}
