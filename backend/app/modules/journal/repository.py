from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.journal.models import JournalEntry
from app.modules.journal.schemas import JournalCreate, JournalUpdate


class JournalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_entries(
        self, user_id: str, entry_type: str | None = None, search: str | None = None
    ) -> list[JournalEntry]:
        q = select(JournalEntry).where(JournalEntry.user_id == user_id)
        if entry_type:
            q = q.where(JournalEntry.entry_type == entry_type)
        if search:
            pattern = f"%{search}%"
            q = q.where(
                or_(
                    JournalEntry.title.ilike(pattern),
                    JournalEntry.content.ilike(pattern),
                    JournalEntry.gratitude.ilike(pattern),
                )
            )
        q = q.order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, entry_id: str) -> JournalEntry | None:
        result = await self.db.execute(
            select(JournalEntry).where(JournalEntry.id == entry_id, JournalEntry.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: JournalCreate) -> JournalEntry:
        entry = JournalEntry(
            user_id=user_id,
            entry_date=data.entry_date,
            entry_type=data.entry_type,
            title=data.title,
            content=data.content,
            gratitude=data.gratitude,
            wins=data.wins,
            lessons=data.lessons,
        )
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def update(self, entry: JournalEntry, data: JournalUpdate) -> JournalEntry:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(entry, key, value)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def delete(self, entry: JournalEntry) -> None:
        await self.db.delete(entry)
        await self.db.flush()
