"""Trips, itinerary and the draft lifecycle (spec §10–§12, §21; requirements D-12, D-13)."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, get_or_404
from app.core.pagination import Pagination
from app.core.timezone import start_of_day_utc, utc_now
from app.modules.calendar.sync_service import CalendarSyncService
from app.modules.travel.itinerary import InvalidOrder, ItemRef, Stop, apply_order, stop_sequence, stops_fingerprint
from app.modules.travel.lifecycle import can_transition, promoted_status, reverted_status, visited_status
from app.modules.travel.models import TravelItineraryDay, TravelItineraryItem, TravelTrip
from app.modules.travel.repository.places import PlaceRepository
from app.modules.travel.repository.routes import RouteRepository
from app.modules.travel.repository.trips import TripRepository
from app.modules.travel.schemas.trips import (
    MAX_TRIP_DAYS,
    DayCreate,
    DayOut,
    DayUpdate,
    ItemCreate,
    ItemOut,
    ItemUpdate,
    ItineraryOrder,
    RouteOut,
    StopOut,
    TripCreate,
    TripDetail,
    TripListItem,
    TripPlaceOut,
    TripSummary,
    TripUpdate,
    check_trip_dates,
)

CALENDAR_SOURCE = "travel"
NOT_FOUND = "Trip not found"


class TripService:
    def __init__(self, db: AsyncSession):
        self.repo = TripRepository(db)
        self.places = PlaceRepository(db)
        self.routes = RouteRepository(db)
        self.calendar = CalendarSyncService(db)

    async def _require(self, user_id: str, trip_id: str) -> TravelTrip:
        return get_or_404(await self.repo.get(user_id, trip_id), NOT_FOUND)

    async def _require_place(self, user_id: str, place_id: str) -> None:
        if not await self.places.owned_ids(user_id, {place_id}):
            raise BadRequestError("Unknown place")

    # ---- trips ------------------------------------------------------------------------------

    async def list_trips(
        self, user_id: str, status: str | None, pagination: Pagination
    ) -> tuple[list[TripListItem], int]:
        trips, total = await self.repo.list_trips(user_id, status, pagination)
        counts = await self.repo.place_counts([t.id for t in trips])
        return [
            TripListItem(**TripSummary.model_validate(t).model_dump(), place_count=counts.get(t.id, 0)) for t in trips
        ], total

    async def create(self, user_id: str, data: TripCreate) -> TripDetail:
        trip = await self.repo.add(TravelTrip(user_id=user_id, status="draft", **data.model_dump()))
        return await self.detail(user_id, trip.id)

    async def update(self, user_id: str, trip_id: str, data: TripUpdate) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        fields = data.model_dump(exclude_unset=True)
        if fields.get("name", "") is None:
            fields.pop("name")
        start = fields.get("start_date", trip.start_date)
        end = fields.get("end_date", trip.end_date)
        try:
            check_trip_dates(start, end)
        except ValueError as exc:
            raise BadRequestError(str(exc)) from exc
        if trip.status != "draft" and (start is None or end is None):
            raise BadRequestError("A confirmed trip needs both dates; move it back to draft first")
        for key, value in fields.items():
            setattr(trip, key, value)
        await self.repo.flush()
        if "start_date" in fields:
            await self._redate_days(trip)
        await self._sync_calendar(trip)
        return await self.detail(user_id, trip.id)

    async def delete(self, user_id: str, trip_id: str) -> None:
        trip = await self._require(user_id, trip_id)
        await self.calendar.delete_from_source(user_id, CALENDAR_SOURCE, trip.id)
        await self.repo.delete(trip)

    # ---- lifecycle --------------------------------------------------------------------------

    async def confirm(self, user_id: str, trip_id: str) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        if trip.status != "draft":
            raise ConflictError("Only a draft trip can be confirmed")
        if trip.start_date is None or trip.end_date is None:
            raise BadRequestError("Set start and end dates before confirming the plan")
        for link, place in await self.repo.trip_places(trip.id):
            new_status = promoted_status(place.status)
            if new_status:
                place.status = new_status
                link.promoted_place = True
        trip.status = "planning"
        trip.dates_tentative = False
        trip.confirmed_at = utc_now()
        await self.repo.flush()
        await self._sync_calendar(trip)
        return await self.detail(user_id, trip.id)

    async def back_to_draft(self, user_id: str, trip_id: str) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        if not can_transition(trip.status, "draft"):
            raise ConflictError("This trip cannot go back to draft")
        for link, place in await self.repo.trip_places(trip.id):
            new_status = reverted_status(place.status, link.promoted_place)
            if new_status:
                place.status = new_status
            link.promoted_place = False
        trip.status = "draft"
        trip.confirmed_at = None
        await self.repo.flush()
        await self._sync_calendar(trip)
        return await self.detail(user_id, trip.id)

    async def set_status(self, user_id: str, trip_id: str, status: str) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        if trip.status == "draft" or not can_transition(trip.status, status):
            raise ConflictError(f"Cannot move a {trip.status} trip to {status}")
        trip.status = status
        await self.repo.flush()
        return await self.detail(user_id, trip.id)

    async def complete(self, user_id: str, trip_id: str) -> TripDetail:
        """Places become visited; routes, photos and journal all remain (spec §21)."""
        trip = await self._require(user_id, trip_id)
        if not can_transition(trip.status, "completed"):
            raise ConflictError("Confirm the plan before completing the trip")
        for link, place in await self.repo.trip_places(trip.id):
            new_status = visited_status(place.status)
            if new_status:
                place.status = new_status
            link.promoted_place = False
        trip.status = "completed"
        trip.completed_at = utc_now()
        await self.repo.flush()
        await self._sync_calendar(trip)
        return await self.detail(user_id, trip.id)

    async def _sync_calendar(self, trip: TravelTrip) -> None:
        """Only confirmed trips with dates appear in the Calendar (requirements D-13)."""
        if trip.status == "draft" or trip.start_date is None or trip.end_date is None:
            await self.calendar.delete_from_source(trip.user_id, CALENDAR_SOURCE, trip.id)
            return
        await self.calendar.upsert_from_source(
            user_id=trip.user_id,
            source_module=CALENDAR_SOURCE,
            source_id=trip.id,
            title=f"🧳 {trip.name}",
            starts_at=start_of_day_utc(trip.start_date),
            ends_at=start_of_day_utc(trip.end_date),
            all_day=True,
            category="personal",
            description=trip.description,
        )

    # ---- places -----------------------------------------------------------------------------

    async def add_place(self, user_id: str, trip_id: str, place_id: str, day_id: str | None) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        await self._require_place(user_id, place_id)
        link = await self.repo.add_link(trip.id, place_id)
        if trip.status != "draft":
            place = (await self.places.get_many(user_id, {place_id}))[place_id]
            new_status = promoted_status(place.status)
            if new_status:
                place.status = new_status
                link.promoted_place = True
        if day_id:
            day = get_or_404(await self.repo.get_day(trip.id, day_id), "Day not found")
            place = (await self.places.get_many(user_id, {place_id}))[place_id]
            await self.repo.add_item(
                TravelItineraryItem(
                    trip_id=trip.id,
                    day_id=day.id,
                    position=await self.repo.next_position(day.id),
                    place_id=place_id,
                    title=place.name,
                )
            )
        await self.repo.flush()
        return await self.detail(user_id, trip.id)

    async def remove_place(self, user_id: str, trip_id: str, place_id: str) -> TripDetail:
        """Removes the place and its stops from this trip (the place itself stays saved)."""
        trip = await self._require(user_id, trip_id)
        link = get_or_404(await self.repo.get_link(trip.id, place_id), "Place is not in this trip")
        place = (await self.places.get_many(user_id, {place_id})).get(place_id)
        if place is not None:
            new_status = reverted_status(place.status, link.promoted_place)
            if new_status:
                place.status = new_status
        await self.repo.remove_link(trip.id, place_id)
        return await self.detail(user_id, trip.id)

    # ---- days -------------------------------------------------------------------------------

    async def add_day(self, user_id: str, trip_id: str, data: DayCreate) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        days = await self.repo.days(trip.id)
        if len(days) >= MAX_TRIP_DAYS:
            raise BadRequestError(f"A trip can have at most {MAX_TRIP_DAYS} days")
        index = days[-1].day_index + 1 if days else 0
        await self.repo.add_days([TravelItineraryDay(trip_id=trip.id, day_index=index, **data.model_dump())])
        await self._redate_days(trip)
        return await self.detail(user_id, trip.id)

    async def fill_days(self, user_id: str, trip_id: str) -> TripDetail:
        """ "Create itinerary": one day per date in the trip (existing days and their plans are kept)."""
        trip = await self._require(user_id, trip_id)
        if trip.start_date is None or trip.end_date is None:
            raise BadRequestError("Set start and end dates first")
        span = (trip.end_date - trip.start_date).days + 1
        existing = await self.repo.days(trip.id)
        start_index = existing[-1].day_index + 1 if existing else 0
        missing = span - len(existing)
        if missing > 0:
            await self.repo.add_days(
                [TravelItineraryDay(trip_id=trip.id, day_index=start_index + i) for i in range(missing)]
            )
        await self._redate_days(trip)
        return await self.detail(user_id, trip.id)

    async def update_day(self, user_id: str, trip_id: str, day_id: str, data: DayUpdate) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        day = get_or_404(await self.repo.get_day(trip.id, day_id), "Day not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(day, key, value)
        await self.repo.flush()
        return await self.detail(user_id, trip.id)

    async def delete_day(self, user_id: str, trip_id: str, day_id: str) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        day = get_or_404(await self.repo.get_day(trip.id, day_id), "Day not found")
        await self.repo.delete_day(day)
        # Close the gap one row at a time (ascending) so (trip_id, day_index) stays unique throughout.
        for index, remaining in enumerate(await self.repo.days(trip.id)):
            if remaining.day_index != index:
                remaining.day_index = index
                await self.repo.flush()
        await self._redate_days(trip)
        return await self.detail(user_id, trip.id)

    async def _redate_days(self, trip: TravelTrip) -> None:
        """Changing trip dates updates every day's date (spec §12)."""
        for day in await self.repo.days(trip.id):
            day.day_date = trip.start_date + timedelta(days=day.day_index) if trip.start_date else None
        await self.repo.flush()

    # ---- items ------------------------------------------------------------------------------

    async def add_item(self, user_id: str, trip_id: str, data: ItemCreate) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        day = get_or_404(await self.repo.get_day(trip.id, data.day_id), "Day not found")
        if data.place_id:
            await self._require_place(user_id, data.place_id)
            await self.repo.add_link(trip.id, data.place_id)
        await self.repo.add_item(
            TravelItineraryItem(
                trip_id=trip.id,
                position=await self.repo.next_position(day.id),
                **data.model_dump(),
            )
        )
        return await self.detail(user_id, trip.id)

    async def update_item(self, user_id: str, trip_id: str, item_id: str, data: ItemUpdate) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        item = get_or_404(await self.repo.get_item(trip.id, item_id), "Itinerary item not found")
        fields = data.model_dump(exclude_unset=True)
        if fields.get("title", "") is None:
            fields.pop("title")
        if fields.get("links", []) is None:
            fields["links"] = []
        if fields.get("place_id"):
            await self._require_place(user_id, fields["place_id"])
            await self.repo.add_link(trip.id, fields["place_id"])
        for key, value in fields.items():
            setattr(item, key, value)
        await self.repo.flush()
        return await self.detail(user_id, trip.id)

    async def delete_item(self, user_id: str, trip_id: str, item_id: str) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        item = get_or_404(await self.repo.get_item(trip.id, item_id), "Itinerary item not found")
        await self.repo.delete_item(item)
        return await self.detail(user_id, trip.id)

    async def reorder(self, user_id: str, trip_id: str, data: ItineraryOrder) -> TripDetail:
        """One request per drag: reorder within a day or move an item to another day (spec §11)."""
        trip = await self._require(user_id, trip_id)
        days = await self.repo.days(trip.id)
        items = await self.repo.items(trip.id)
        try:
            layout = apply_order([d.id for d in days], [_ref(i) for i in items], data.days)
        except InvalidOrder as exc:
            raise BadRequestError(str(exc)) from exc
        for item in items:
            item.day_id, item.position = layout[item.id]
        await self.repo.flush()
        return await self.detail(user_id, trip.id)

    # ---- read model -------------------------------------------------------------------------

    async def stops(self, user_id: str, trip_id: str) -> tuple[TravelTrip, list[Stop]]:
        trip = await self._require(user_id, trip_id)
        return trip, await self._stops(user_id, trip)

    async def _stops(self, user_id: str, trip: TravelTrip) -> list[Stop]:
        days = await self.repo.days(trip.id)
        items = await self.repo.items(trip.id)
        place_ids = {i.place_id for i in items if i.place_id}
        places = await self.places.get_many(user_id, place_ids)
        return stop_sequence(
            [d.id for d in days],
            [_ref(i) for i in items],
            {pid: (p.name, p.lat, p.lng) for pid, p in places.items()},
        )

    async def detail(self, user_id: str, trip_id: str) -> TripDetail:
        trip = await self._require(user_id, trip_id)
        days = await self.repo.days(trip.id)
        items = await self.repo.items(trip.id)
        by_day: dict[str, list[ItemOut]] = {}
        for item in sorted(items, key=lambda i: i.position):
            out = ItemOut.model_validate(item).model_copy(update={"links": item.links or []})
            by_day.setdefault(item.day_id, []).append(out)
        stops = await self._stops(user_id, trip)
        route = await self.routes.for_trip(trip.id)
        route_out = None
        if route is not None:
            stale = route.stops_fingerprint != stops_fingerprint(stops, route.mode)
            route_out = RouteOut.model_validate(route).model_copy(update={"is_stale": stale})
        return TripDetail(
            trip=TripSummary.model_validate(trip),
            days=[
                DayOut(
                    id=d.id,
                    day_index=d.day_index,
                    day_date=d.day_date,
                    title=d.title,
                    notes=d.notes,
                    items=by_day.get(d.id, []),
                )
                for d in days
            ],
            places=[
                TripPlaceOut(
                    id=p.id,
                    name=p.name,
                    lat=p.lat,
                    lng=p.lng,
                    status=p.status,
                    external_place_id=p.external_place_id,
                )
                for _, p in await self.repo.trip_places(trip.id)
            ],
            stops=[StopOut(place_id=s.place_id, name=s.name, lat=s.lat, lng=s.lng) for s in stops],
            route=route_out,
        )


def _ref(item: TravelItineraryItem) -> ItemRef:
    return ItemRef(id=item.id, day_id=item.day_id, position=item.position, place_id=item.place_id)
