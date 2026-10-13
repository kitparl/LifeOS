"""Loads a trip or adventure and renders its shareable PDF guide (see `export_pdf`)."""

from __future__ import annotations

import re

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination
from app.modules.travel.export_pdf import adventure_guide_pdf, plain, trip_guide_pdf
from app.modules.travel.export_plan import plan_document_detail
from app.modules.travel.export_tiles import TileBasemap
from app.modules.travel.repository.adventures import AdventureRepository
from app.modules.travel.repository.places import PlaceRepository
from app.modules.travel.repository.shares import ShareRepository
from app.modules.travel.repository.trips import TripRepository
from app.modules.travel.schemas.adventures import AdventureOut
from app.modules.travel.schemas.plan_document import PlanDocument
from app.modules.travel.services.adventure_service import AdventureService
from app.modules.travel.services.trip_service import TripService

MAX_LINKED_ADVENTURES = 100


class ExportService:
    def __init__(self, db: AsyncSession):
        self.trips = TripService(db)
        self.adventures = AdventureService(db)
        self.adventure_repo = AdventureRepository(db)
        self.trip_repo = TripRepository(db)
        self.places = PlaceRepository(db)
        self.shares = ShareRepository(db)

    async def trip_pdf(self, user_id: str, trip_id: str, origin: str | None = None) -> tuple[bytes, str]:
        """`origin` (the app's public origin) adds the trip's active share link to the footer."""
        detail = await self.trips.detail(user_id, trip_id)
        places = await self.places.get_many(user_id, {p.id for p in detail.places})
        linked, _ = await self.adventure_repo.list_adventures(
            user_id, trip_id, Pagination(limit=MAX_LINKED_ADVENTURES, offset=0)
        )
        adventures = [AdventureOut.model_validate(a) for a in linked]
        # Rendering fetches map tiles over the network, so it runs off the event loop.
        share = await self.shares.get_for_trip(user_id, trip_id) if origin else None
        share_url = f"{origin}/t/{share.code}" if share is not None and share.state != "revoked" else None
        pdf = await run_in_threadpool(
            trip_guide_pdf, detail, places, adventures, TileBasemap.from_settings(), share_url
        )
        return pdf, file_name(detail.trip.name, "trip")

    async def plan_pdf(self, user_id: str, trip_id: str, doc: PlanDocument, label: str) -> tuple[bytes, str]:
        """The PDF guide of a shared plan version, before (or without) applying it to the trip."""
        trip = (await self.trips.detail(user_id, trip_id)).trip
        detail, places = plan_document_detail(trip, doc)
        pdf = await run_in_threadpool(trip_guide_pdf, detail, places, [], TileBasemap.from_settings())
        return pdf, file_name(f"{detail.trip.name} {label}", "plan")

    async def adventure_pdf(self, user_id: str, adventure_id: str) -> tuple[bytes, str]:
        detail = await self.adventures.detail(user_id, adventure_id)
        trip = await self.trip_repo.get(user_id, detail.adventure.trip_id) if detail.adventure.trip_id else None
        pdf = await run_in_threadpool(
            adventure_guide_pdf, detail, trip.name if trip else None, TileBasemap.from_settings()
        )
        return pdf, file_name(detail.adventure.name, "adventure")


def file_name(name: str, fallback: str) -> str:
    """ASCII-only download name, safe inside a Content-Disposition header."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", plain(name)).strip("-")
    return f"{slug or fallback}-guide.pdf"
