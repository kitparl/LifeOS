from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import get_or_404
from app.modules.sticky_notes.repository import StickyNoteRepository
from app.modules.sticky_notes.schemas import (
    StickyNoteCreate,
    StickyNoteMonth,
    StickyNoteResponse,
    StickyNoteUpdate,
)

STICKY_NOTES_PURGE_AFTER_DAYS = 60

class StickyNoteService:
    def __init__(self, db: AsyncSession):
        self.repo = StickyNoteRepository(db)

    async def list_months(self, user_id: str) -> list[StickyNoteMonth]:
        await self.purge_expired()
        return [StickyNoteMonth(month=m, note_count=c) for m, c in await self.repo.list_months(user_id)]

    async def list_all(self, user_id: str) -> list[StickyNoteResponse]:
        await self.purge_expired()
        notes = await self.repo.list_all(user_id)
        return [StickyNoteResponse.model_validate(n) for n in notes]

    async def list_deleted(self, user_id: str) -> list[StickyNoteResponse]:
        await self.purge_expired()
        notes = await self.repo.list_deleted(user_id)
        return [StickyNoteResponse.model_validate(n) for n in notes]

    async def list_by_month(self, user_id: str, month: str) -> list[StickyNoteResponse]:
        await self.purge_expired()
        notes = await self.repo.list_by_month(user_id, month)
        return [StickyNoteResponse.model_validate(n) for n in notes]

    async def list_recent(self, user_id: str, limit: int = 5) -> list[StickyNoteResponse]:
        notes = await self.repo.list_recent(user_id, limit)
        return [StickyNoteResponse.model_validate(n) for n in notes]

    async def search(self, user_id: str, query: str) -> list[StickyNoteResponse]:
        clean = query.strip()
        if not clean:
            return []
        notes = await self.repo.search(user_id, clean)
        return [StickyNoteResponse.model_validate(n) for n in notes]

    async def get_note(self, user_id: str, note_id: str) -> StickyNoteResponse:
        await self.purge_expired()
        note = get_or_404(await self.repo.get_by_id(user_id, note_id), "Note not found")
        return StickyNoteResponse.model_validate(note)

    async def create_note(self, user_id: str, data: StickyNoteCreate) -> StickyNoteResponse:
        month = datetime.now(UTC).strftime("%Y-%m")
        current_min = await self.repo.min_order_index(user_id, month)
        # New notes get an index below every existing note in the month, so
        # "newest first" is the default outcome without any manual reorder.
        next_index = (current_min - 1) if current_min is not None else 0
        note = await self.repo.create(user_id, month, next_index, data)
        return StickyNoteResponse.model_validate(note)

    async def update_note(self, user_id: str, note_id: str, data: StickyNoteUpdate) -> StickyNoteResponse:
        note = get_or_404(await self.repo.get_by_id(user_id, note_id), "Note not found")
        updated = await self.repo.update(note, data)
        return StickyNoteResponse.model_validate(updated)

    async def delete_note(self, user_id: str, note_id: str) -> None:
        await self.purge_expired()
        note = get_or_404(await self.repo.get_by_id(user_id, note_id), "Note not found")
        await self.repo.soft_delete(note)

    async def restore_note(self, user_id: str, note_id: str) -> StickyNoteResponse:
        await self.purge_expired()
        note = get_or_404(
            await self.repo.get_by_id(user_id, note_id, include_deleted=True), "Note not found"
        )
        if note.deleted_at is not None:
            await self.repo.restore(note)
        return StickyNoteResponse.model_validate(note)

    async def purge_expired(self, days: int | None = None) -> int:
        return await self.repo.purge_expired(days if days is not None else STICKY_NOTES_PURGE_AFTER_DAYS)
