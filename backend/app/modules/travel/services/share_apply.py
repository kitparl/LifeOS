"""Turning a shared plan into the real trip (requirements T-21). The only share code that writes trip tables.

Runs inside the request's single transaction (`get_db` commits once at the end), so a failure
leaves the trip, the backup and the lock exactly as they were.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import new_id
from app.core.timezone import as_utc, utc_now
from app.modules.travel.geo import round_coord
from app.modules.travel.lifecycle import promoted_status
from app.modules.travel.models import (
    TravelItineraryDay,
    TravelItineraryItem,
    TravelPlace,
    TravelShareVersion,
    TravelTrip,
    TravelTripShare,
)
from app.modules.travel.plan_document import applied_end_date, apply_rows, backups_to_prune, snapshot_from_trip
from app.modules.travel.repository.places import PlaceRepository
from app.modules.travel.repository.shares import ShareRepository
from app.modules.travel.repository.trips import TripRepository
from app.modules.travel.schemas.plan_document import PlanDocument, PlanPlace
from app.modules.travel.schemas.shares import ApplyResult
from app.modules.travel.schemas.trips import TripUpdate
from app.modules.travel.services.trip_service import TripService

LABEL_MAX = 80


@dataclass
class _PlaceTally:
    created: int = 0
    reused: int = 0


class ShareApplyService:
    def __init__(self, db: AsyncSession):
        self.trips = TripService(db)
        self.trip_repo = TripRepository(db)
        self.places = PlaceRepository(db)
        self.repo = ShareRepository(db)

    async def trip_document(self, user_id: str, trip_id: str) -> PlanDocument:
        """The live trip as a plan document (the Original, owner snapshots and backups)."""
        detail = await self.trips.detail(user_id, trip_id)
        place_ids = {item.place_id for day in detail.days for item in day.items if item.place_id}
        places = await self.places.get_many(user_id, place_ids)
        return snapshot_from_trip(detail.days, places)

    async def apply(self, trip: TravelTrip, share: TravelTripShare, version: TravelShareVersion) -> ApplyResult:
        doc = PlanDocument.model_validate(version.document)
        backup = await self._backup(trip, share, version.label)
        tally = _PlaceTally()
        place_ids: dict[tuple, str] = {}

        await self.trip_repo.clear_itinerary(trip.id)
        days: list[TravelItineraryDay] = []
        items: list[TravelItineraryItem] = []
        for row in apply_rows(doc, trip.start_date):
            day = TravelItineraryDay(
                id=new_id(), trip_id=trip.id, day_index=row.day_index, day_date=row.day_date, title=row.title,
                notes=row.notes,
            )
            days.append(day)
            for item in row.items:
                place_id = await self._place_for(trip, item.place, place_ids, tally) if item.place else None
                items.append(
                    TravelItineraryItem(
                        trip_id=trip.id,
                        day_id=day.id,
                        position=item.position,
                        place_id=place_id,
                        title=item.title,
                        start_time=item.start_time,
                        end_time=item.end_time,
                        transport=item.transport,
                        accommodation=item.accommodation,
                        notes=item.notes,
                        links=item.links,
                    )
                )
        await self.trip_repo.add_days(days)
        await self.trip_repo.add_items(items)

        new_end = applied_end_date(trip.start_date, trip.end_date, len(days))
        end_changed = new_end != trip.end_date
        if end_changed:
            # Same path as editing the dates by hand: validation, day dates and the Calendar mirror.
            await self.trips.update(trip.user_id, trip.id, TripUpdate(end_date=new_end))
        return ApplyResult(
            days=len(days),
            items=len(items),
            places_created=tally.created,
            places_reused=tally.reused,
            backup_version_id=backup.id,
            end_date=trip.end_date,
            end_date_changed=end_changed,
        )

    async def _backup(self, trip: TravelTrip, share: TravelTripShare, label: str) -> TravelShareVersion:
        now = utc_now()
        backup = TravelShareVersion(
            share_id=share.id,
            kind="backup",
            label=f"Before applying {label}"[:LABEL_MAX],
            document=(await self.trip_document(trip.user_id, trip.id)).model_dump(mode="json"),
            created_at=now,
            updated_at=now,
        )
        await self.repo.add(backup)
        backups = await self.repo.versions_of_kind(share.id, "backup")
        stale = set(backups_to_prune([(b.id, as_utc(b.created_at)) for b in backups]))
        for old in backups:
            if old.id in stale:
                await self.repo.delete_version(old)
        return backup

    async def _place_for(
        self, trip: TravelTrip, place: PlanPlace, seen: dict[tuple, str], tally: _PlaceTally
    ) -> str:
        """An owner place for this stop: reuse a saved one (same Google id or same spot), else create it."""
        lat, lng = round_coord(place.lat), round_coord(place.lng)
        key = (place.google_place_id or "", lat, lng)
        if key in seen:
            return seen[key]
        existing = await self.places.find_duplicate(
            trip.user_id, external_place_id=place.google_place_id, lat=lat, lng=lng
        )
        if existing is not None:
            saved = existing
            tally.reused += 1
        else:
            saved = await self.places.add(
                TravelPlace(
                    user_id=trip.user_id,
                    name=place.name,
                    lat=lat,
                    lng=lng,
                    external_place_id=place.google_place_id,
                    external_source="google" if place.google_place_id else None,
                )
            )
            tally.created += 1
        link = await self.trip_repo.add_link(trip.id, saved.id)
        if trip.status != "draft":
            new_status = promoted_status(saved.status)
            if new_status:
                saved.status = new_status
                link.promoted_place = True
        seen[key] = saved.id
        return saved.id
