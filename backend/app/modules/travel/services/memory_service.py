"""Photos (stored through the Files module) and the travel journal (spec §17–§19, requirements D-06/D-08)."""

from __future__ import annotations

from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import new_id
from app.core.exceptions import BadRequestError, get_or_404
from app.core.pagination import Pagination
from app.modules.files.service import FileService
from app.modules.travel.models import TravelJournalEntry, TravelPhoto
from app.modules.travel.repository.memories import LINK_MODELS, MemoryRepository
from app.modules.travel.schemas.memories import (
    JournalCreate,
    JournalOut,
    JournalUpdate,
    PhotoMeta,
    PhotoOut,
    PhotoUpdate,
)

PHOTO_FILTERS = ("trip_id", "place_id", "adventure_id", "day_id", "journal_entry_id")


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MemoryRepository(db)

    async def _check_links(self, user_id: str, fields: dict[str, Any]) -> None:
        for column, value in fields.items():
            if not value:
                continue
            if column == "day_id":
                ok = await self.repo.owns_day(user_id, value)
            elif column in LINK_MODELS:
                ok = await self.repo.owns(user_id, LINK_MODELS[column], value)
            else:
                continue
            if not ok:
                raise BadRequestError(f"Unknown {column.removesuffix('_id').replace('_', ' ')}")

    # ---- photos ------------------------------------------------------------------------------

    async def upload_photo(self, user_id: str, upload: UploadFile, meta: PhotoMeta) -> PhotoOut:
        await self._check_links(user_id, meta.model_dump())
        photo_id = new_id()
        files = FileService(self.db)
        stored = await files.upload_file(user_id, upload, module="travel", entity_id=photo_id)
        if not stored.content_type.startswith("image/"):
            await files.delete_file(user_id, stored.id)
            raise BadRequestError("Travel photos must be images")
        photo = TravelPhoto(id=photo_id, user_id=user_id, file_id=stored.id, **meta.model_dump())
        await self.repo.add(photo)
        return PhotoOut.model_validate(photo)

    async def list_photos(
        self, user_id: str, filters: dict[str, str | None], has_location: bool | None, pagination: Pagination
    ) -> tuple[list[PhotoOut], int]:
        photos, total = await self.repo.list_photos(user_id, filters, has_location, pagination)
        return [PhotoOut.model_validate(p) for p in photos], total

    async def update_photo(self, user_id: str, photo_id: str, data: PhotoUpdate) -> PhotoOut:
        photo = get_or_404(await self.repo.get_photo(user_id, photo_id), "Photo not found")
        fields = data.model_dump(exclude_unset=True)
        await self._check_links(user_id, fields)
        if ("lat" in fields) != ("lng" in fields):
            raise BadRequestError("lat and lng go together")
        if "lat" in fields and (fields["lat"] is None) != (fields["lng"] is None):
            raise BadRequestError("lat and lng go together")
        for key, value in fields.items():
            setattr(photo, key, value)
        if "lat" in fields:
            # A location set or corrected here is the user's own, not EXIF's.
            photo.location_source = "manual" if photo.lat is not None else None
        await self.repo.flush_refresh(photo)
        return PhotoOut.model_validate(photo)

    async def delete_photo(self, user_id: str, photo_id: str) -> None:
        photo = get_or_404(await self.repo.get_photo(user_id, photo_id), "Photo not found")
        await FileService(self.db).delete_file(user_id, photo.file_id)
        await self.repo.delete(photo)

    # ---- journal -----------------------------------------------------------------------------

    async def list_journal(
        self, user_id: str, trip_id: str | None, place_id: str | None, pagination: Pagination
    ) -> tuple[list[JournalOut], int]:
        entries, total = await self.repo.list_journal(user_id, trip_id, place_id, pagination)
        return [JournalOut.model_validate(e) for e in entries], total

    async def get_entry(self, user_id: str, entry_id: str) -> JournalOut:
        return JournalOut.model_validate(get_or_404(await self.repo.get_entry(user_id, entry_id), "Entry not found"))

    async def create_entry(self, user_id: str, data: JournalCreate) -> JournalOut:
        await self._check_links(user_id, data.model_dump())
        entry = TravelJournalEntry(user_id=user_id, **data.model_dump())
        await self.repo.add(entry)
        return JournalOut.model_validate(entry)

    async def update_entry(self, user_id: str, entry_id: str, data: JournalUpdate) -> JournalOut:
        entry = get_or_404(await self.repo.get_entry(user_id, entry_id), "Entry not found")
        fields = data.model_dump(exclude_unset=True)
        for required in ("entry_date", "title", "content"):
            if fields.get(required, "") is None:
                fields.pop(required)
        await self._check_links(user_id, fields)
        for key, value in fields.items():
            setattr(entry, key, value)
        await self.repo.flush_refresh(entry)
        return JournalOut.model_validate(entry)

    async def delete_entry(self, user_id: str, entry_id: str) -> None:
        entry = get_or_404(await self.repo.get_entry(user_id, entry_id), "Entry not found")
        await self.repo.unlink_entry_photos(entry.id)
        await self.repo.delete(entry)
