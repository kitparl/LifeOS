from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, get_or_404
from app.core.pagination import Pagination
from app.core.taxonomy import merge_names
from app.modules.travel.geo import bbox_for_radius, haversine_m, round_coord
from app.modules.travel.models import TravelPlace
from app.modules.travel.repository.places import PlaceRepository
from app.modules.travel.schemas.places import (
    Marker,
    NearPlaceOut,
    PlaceCreate,
    PlaceHistory,
    PlaceHistoryTrip,
    PlaceOut,
    PlaceUpdate,
)

NOT_FOUND = "Place not found"
HISTORY_PHOTO_LIMIT = 12
MAX_NEAR_RADIUS_KM = 5_000


class PlaceService:
    def __init__(self, db: AsyncSession):
        self.repo = PlaceRepository(db)

    async def _out(self, place: TravelPlace) -> PlaceOut:
        tags = await self.repo.tags_for([place.id])
        return _to_out(place, tags.get(place.id, []))

    async def _require(self, user_id: str, place_id: str) -> TravelPlace:
        return get_or_404(await self.repo.get(user_id, place_id), NOT_FOUND)

    async def list_places(
        self,
        user_id: str,
        *,
        status: str | None,
        category: str | None,
        tag: str | None,
        q: str | None,
        pagination: Pagination,
    ) -> tuple[list[PlaceOut], int]:
        places, total = await self.repo.list_places(
            user_id, status=status, category=category, tag=tag, q=q, pagination=pagination
        )
        tags = await self.repo.tags_for([p.id for p in places])
        return [_to_out(p, tags.get(p.id, [])) for p in places], total

    async def get(self, user_id: str, place_id: str) -> PlaceOut:
        return await self._out(await self._require(user_id, place_id))

    async def create(self, user_id: str, data: PlaceCreate) -> PlaceOut:
        lat, lng = round_coord(data.lat), round_coord(data.lng)
        duplicate = await self.repo.find_duplicate(user_id, external_place_id=data.external_place_id, lat=lat, lng=lng)
        if duplicate is not None:
            raise ConflictError({"code": "duplicate", "place_id": duplicate.id, "message": "Place already saved"})
        fields = data.model_dump(exclude={"tags"})
        place = await self.repo.add(
            TravelPlace(
                user_id=user_id,
                **{**fields, "lat": lat, "lng": lng},
                external_source="google" if data.external_place_id else None,
            )
        )
        if data.tags:
            await self.repo.set_tags(user_id, place.id, data.tags)
        return await self._out(place)

    async def update(self, user_id: str, place_id: str, data: PlaceUpdate) -> PlaceOut:
        place = await self._require(user_id, place_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            if key in ("lat", "lng") and value is not None:
                value = round_coord(value)
            if key == "links" and value is None:
                value = []
            if value is None and key in ("name", "lat", "lng", "category", "status"):
                continue  # required columns: an explicit null means "unchanged"
            setattr(place, key, value)
        return await self._out(await self.repo.flush_refresh(place))

    async def delete(self, user_id: str, place_id: str) -> None:
        place = await self._require(user_id, place_id)
        if await self.repo.is_referenced(place.id):
            raise ConflictError("This place is used by a trip or photo. Remove it there first.")
        await self.repo.delete(place)

    async def set_tags(self, user_id: str, place_id: str, names: list[str]) -> PlaceOut:
        place = await self._require(user_id, place_id)
        await self.repo.set_tags(user_id, place.id, names)
        return await self._out(place)

    async def list_tags(self, user_id: str) -> list[str]:
        return merge_names(await self.repo.list_tag_names(user_id))

    async def near(
        self, user_id: str, lat: float, lng: float, radius_km: float, status: str | None
    ) -> list[NearPlaceOut]:
        """Bounding-box SQL prefilter, then the exact haversine check (requirements D-04, spec §32)."""
        radius_m = min(radius_km, MAX_NEAR_RADIUS_KM) * 1000
        candidates = await self.repo.in_bbox(user_id, bbox_for_radius((lat, lng), radius_m), status)
        within = [(p, haversine_m((lat, lng), (p.lat, p.lng))) for p in candidates]
        within = sorted((pd for pd in within if pd[1] <= radius_m), key=lambda pd: pd[1])
        tags = await self.repo.tags_for([p.id for p, _ in within])
        return [NearPlaceOut(**_to_out(p, tags.get(p.id, [])).model_dump(), distance_m=round(d, 1)) for p, d in within]

    async def markers(self, user_id: str) -> list[Marker]:
        return [
            Marker(id=pid, kind="place", lat=lat, lng=lng, label=name, status=status)
            for pid, name, lat, lng, status in await self.repo.markers(user_id)
        ]

    async def history(self, user_id: str, place_id: str) -> PlaceHistory:
        place = await self._require(user_id, place_id)
        trips = await self.repo.trips_for_place(user_id, place.id)
        photo_count, photo_ids = await self.repo.photo_ids_for_place(user_id, place.id, HISTORY_PHOTO_LIMIT)
        return PlaceHistory(
            place=await self._out(place),
            trips=[
                PlaceHistoryTrip(
                    id=t.id, name=t.name, status=t.status, start_date=t.start_date.isoformat() if t.start_date else None
                )
                for t in trips
            ],
            photo_count=photo_count,
            recent_photo_ids=photo_ids,
            journal_count=await self.repo.journal_count_for_place(user_id, place.id),
            route_ids=await self.repo.route_ids_for_place(user_id, place.id),
        )


def _to_out(place: TravelPlace, tags: list[str]) -> PlaceOut:
    out = PlaceOut.model_validate(place)
    return out.model_copy(update={"tags": tags, "links": place.links or []})
