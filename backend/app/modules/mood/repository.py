from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.mood.models import MoodEntry
from app.modules.mood.schemas import MoodUpsert


class MoodRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_entries(self, user_id: str, days: int = 30) -> list[MoodEntry]:
        since = datetime.now(UTC).date() - timedelta(days=days - 1)
        result = await self.db.execute(
            select(MoodEntry)
            .where(MoodEntry.user_id == user_id, MoodEntry.log_date >= since)
            .order_by(MoodEntry.log_date.desc())
        )
        return list(result.scalars().all())

    async def get_by_date(self, user_id: str, log_date: date) -> MoodEntry | None:
        result = await self.db.execute(
            select(MoodEntry).where(MoodEntry.user_id == user_id, MoodEntry.log_date == log_date)
        )
        return result.scalar_one_or_none()

    async def upsert_today(self, user_id: str, data: MoodUpsert) -> MoodEntry:
        today = datetime.now(UTC).date()
        entry = await self.get_by_date(user_id, today)
        if entry is None:
            entry = MoodEntry(
                user_id=user_id,
                log_date=today,
                stress=data.stress,
                confidence=data.confidence,
                motivation=data.motivation,
                happiness=data.happiness,
                notes=data.notes,
            )
            self.db.add(entry)
        else:
            entry.stress = data.stress
            entry.confidence = data.confidence
            entry.motivation = data.motivation
            entry.happiness = data.happiness
            entry.notes = data.notes
        await self.db.flush()
        await self.db.refresh(entry)
        return entry
