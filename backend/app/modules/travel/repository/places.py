from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import taxonomy
from app.core.pagination import Pagination, paginate
from app.modules.travel.geo import BBox
from app.modules.travel.models import (
    TravelItineraryItem,
    TravelJournalEntry,
    TravelPhoto,
    TravelPlace,
    TravelPlaceTag,
    TravelRoute,
    TravelRouteWaypoint,
    TravelTag,
    TravelTrip,
    TravelTripPlace,
)

# Two saves within ~1 m of each other are "the same spot" (dedup, requirements T-02).
_SAME_SPOT_DEG = 0.000_01


class PlaceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_places(
        self,
        user_id: str,
        *,
        status: str | None,
        category: str | None,
        tag: str | None,
        q: str | None,
        pagination: Pagination,
    ) -> tuple[list[TravelPlace], int]:
        stmt = select(TravelPlace).where(TravelPlace.user_id == user_id)
        if status:
            stmt = stmt.where(TravelPlace.status == status)
        if category:
            stmt = stmt.where(TravelPlace.category == category)
        if q:
            like = f"%{q.lower()}%"
            stmt = stmt.where(or_(func.lower(TravelPlace.name).like(like), func.lower(TravelPlace.address).like(like)))
        if tag:
            stmt = stmt.where(
                TravelPlace.id.in_(
                    select(TravelPlaceTag.place_id)
                    .join(TravelTag, TravelTag.id == TravelPlaceTag.tag_id)
                    .where(TravelTag.user_id == user_id, func.lower(TravelTag.name) == tag.lower())
                )
            )
        stmt = stmt.order_by(TravelPlace.updated_at.desc())
        return await paginate(self.db, stmt, pagination)

    async def get(self, user_id: str, place_id: str) -> TravelPlace | None:
        result = await self.db.execute(
            select(TravelPlace).where(TravelPlace.id == place_id, TravelPlace.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def owned_ids(self, user_id: str, place_ids: set[str]) -> set[str]:
        if not place_ids:
            return set()
        result = await self.db.execute(
            select(TravelPlace.id).where(TravelPlace.user_id == user_id, TravelPlace.id.in_(place_ids))
        )
        return set(result.scalars().all())

    async def get_many(self, user_id: str, place_ids: set[str]) -> dict[str, TravelPlace]:
        if not place_ids:
            return {}
        result = await self.db.execute(
            select(TravelPlace).where(TravelPlace.user_id == user_id, TravelPlace.id.in_(place_ids))
        )
        return {p.id: p for p in result.scalars().all()}

    async def find_duplicate(
        self, user_id: str, *, external_place_id: str | None, lat: float, lng: float
    ) -> TravelPlace | None:
        conditions = [
            (TravelPlace.lat.between(lat - _SAME_SPOT_DEG, lat + _SAME_SPOT_DEG))
            & (TravelPlace.lng.between(lng - _SAME_SPOT_DEG, lng + _SAME_SPOT_DEG))
        ]
        if external_place_id:
            conditions.append(TravelPlace.external_place_id == external_place_id)
        result = await self.db.execute(
            select(TravelPlace).where(TravelPlace.user_id == user_id, or_(*conditions)).limit(1)
        )
        return result.scalar_one_or_none()

    async def in_bbox(self, user_id: str, box: BBox, status: str | None) -> list[TravelPlace]:
        lng_filter = (
            or_(TravelPlace.lng >= box.min_lng, TravelPlace.lng <= box.max_lng)
            if box.wraps
            else TravelPlace.lng.between(box.min_lng, box.max_lng)
        )
        stmt = select(TravelPlace).where(
            TravelPlace.user_id == user_id, TravelPlace.lat.between(box.min_lat, box.max_lat), lng_filter
        )
        if status:
            stmt = stmt.where(TravelPlace.status == status)
        return list((await self.db.execute(stmt)).scalars().all())

    async def markers(self, user_id: str) -> list[tuple[str, str, float, float, str]]:
        result = await self.db.execute(
            select(TravelPlace.id, TravelPlace.name, TravelPlace.lat, TravelPlace.lng, TravelPlace.status).where(
                TravelPlace.user_id == user_id
            )
        )
        return [tuple(row) for row in result.all()]

    async def add(self, place: TravelPlace) -> TravelPlace:
        self.db.add(place)
        await self.db.flush()
        await self.db.refresh(place)
        return place

    async def flush_refresh(self, place: TravelPlace) -> TravelPlace:
        await self.db.flush()
        await self.db.refresh(place)
        return place

    async def delete(self, place: TravelPlace) -> None:
        await self.db.execute(delete(TravelPlaceTag).where(TravelPlaceTag.place_id == place.id))
        await self.db.delete(place)
        await self.db.flush()

    async def is_referenced(self, place_id: str) -> bool:
        """Used by a trip, itinerary stop or photo (deleting it would silently break those)."""
        for model, column in (
            (TravelTripPlace, TravelTripPlace.place_id),
            (TravelItineraryItem, TravelItineraryItem.place_id),
            (TravelPhoto, TravelPhoto.place_id),
        ):
            found = await self.db.scalar(select(func.count()).select_from(model).where(column == place_id))
            if found:
                return True
        return False

    # ---- tags -------------------------------------------------------------------------------

    async def list_tag_names(self, user_id: str) -> list[str]:
        return await taxonomy.list_names(self.db, TravelTag, user_id)

    async def tags_for(self, place_ids: list[str]) -> dict[str, list[str]]:
        if not place_ids:
            return {}
        result = await self.db.execute(
            select(TravelPlaceTag.place_id, TravelTag.name)
            .join(TravelTag, TravelTag.id == TravelPlaceTag.tag_id)
            .where(TravelPlaceTag.place_id.in_(place_ids))
        )
        out: dict[str, list[str]] = {}
        for place_id, name in result.all():
            out.setdefault(place_id, []).append(name)
        return {pid: sorted(names, key=str.lower) for pid, names in out.items()}

    async def set_tags(self, user_id: str, place_id: str, names: list[str]) -> None:
        for name in names:
            await taxonomy.ensure_name(self.db, TravelTag, user_id, name)
        wanted = {n.lower() for n in names}
        result = await self.db.execute(select(TravelTag).where(TravelTag.user_id == user_id))
        tag_ids = [t.id for t in result.scalars().all() if t.name.lower() in wanted]
        await self.db.execute(delete(TravelPlaceTag).where(TravelPlaceTag.place_id == place_id))
        self.db.add_all([TravelPlaceTag(place_id=place_id, tag_id=tid) for tid in tag_ids])
        await self.db.flush()

    # ---- history (spec §20) -------------------------------------------------------------------

    async def trips_for_place(self, user_id: str, place_id: str) -> list[TravelTrip]:
        via_items = select(TravelItineraryItem.trip_id).where(TravelItineraryItem.place_id == place_id)
        via_links = select(TravelTripPlace.trip_id).where(TravelTripPlace.place_id == place_id)
        result = await self.db.execute(
            select(TravelTrip)
            .where(TravelTrip.user_id == user_id, or_(TravelTrip.id.in_(via_items), TravelTrip.id.in_(via_links)))
            .order_by(TravelTrip.start_date.desc().nulls_last(), TravelTrip.created_at.desc())
        )
        return list(result.scalars().all())

    async def photo_ids_for_place(self, user_id: str, place_id: str, limit: int) -> tuple[int, list[str]]:
        base = select(TravelPhoto).where(TravelPhoto.user_id == user_id, TravelPhoto.place_id == place_id)
        count = await self.db.scalar(select(func.count()).select_from(base.subquery()))
        result = await self.db.execute(
            base.with_only_columns(TravelPhoto.id).order_by(TravelPhoto.created_at.desc()).limit(limit)
        )
        return int(count or 0), list(result.scalars().all())

    async def journal_count_for_place(self, user_id: str, place_id: str) -> int:
        count = await self.db.scalar(
            select(func.count())
            .select_from(TravelJournalEntry)
            .where(TravelJournalEntry.user_id == user_id, TravelJournalEntry.place_id == place_id)
        )
        return int(count or 0)

    async def route_ids_for_place(self, user_id: str, place_id: str) -> list[str]:
        result = await self.db.execute(
            select(TravelRoute.id)
            .join(TravelRouteWaypoint, TravelRouteWaypoint.route_id == TravelRoute.id)
            .where(TravelRoute.user_id == user_id, TravelRouteWaypoint.place_id == place_id)
            .distinct()
        )
        return list(result.scalars().all())
