from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.modules.voice.models import VoiceNote
from app.modules.voice.schemas import VoiceNoteCreate


class VoiceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_notes(
        self, user_id: str, limit: int = 25, offset: int = 0
    ) -> tuple[list[VoiceNote], int]:
        q = (
            select(VoiceNote)
            .where(VoiceNote.user_id == user_id)
            .order_by(VoiceNote.created_at.desc())
        )
        return await paginate(self.db, q, Pagination(limit=limit, offset=offset))

    async def create(self, user_id: str, data: VoiceNoteCreate, command_result: str | None = None) -> VoiceNote:
        note = VoiceNote(
            user_id=user_id,
            title=data.title,
            transcript=data.transcript,
            note_type=data.note_type,
            audio_file_id=data.audio_file_id,
            command_result=command_result,
        )
        self.db.add(note)
        await self.db.flush()
        await self.db.refresh(note)
        return note

    async def delete(self, user_id: str, note_id: str) -> VoiceNote | None:
        result = await self.db.execute(
            select(VoiceNote).where(VoiceNote.id == note_id, VoiceNote.user_id == user_id)
        )
        note = result.scalar_one_or_none()
        if note:
            await self.db.delete(note)
        return note
