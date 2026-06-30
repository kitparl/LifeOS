from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.mood.repository import MoodRepository
from app.modules.mood.schemas import MoodResponse, MoodStats, MoodUpsert


class MoodService:
    def __init__(self, db: AsyncSession):
        self.repo = MoodRepository(db)

    async def list_entries(self, user_id: str, days: int = 30) -> list[MoodResponse]:
        entries = await self.repo.list_entries(user_id, days=days)
        return [MoodResponse.model_validate(e) for e in entries]

    async def get_today(self, user_id: str) -> MoodResponse | None:
        today = datetime.now(UTC).date()
        entry = await self.repo.get_by_date(user_id, today)
        return MoodResponse.model_validate(entry) if entry else None

    async def upsert_today(self, user_id: str, data: MoodUpsert) -> MoodResponse:
        entry = await self.repo.upsert_today(user_id, data)
        return MoodResponse.model_validate(entry)

    async def get_stats(self, user_id: str, days: int = 7) -> MoodStats:
        entries = await self.repo.list_entries(user_id, days=days)
        if not entries:
            return MoodStats(
                days=days,
                avg_stress=0,
                avg_confidence=0,
                avg_motivation=0,
                avg_happiness=0,
                recent=[],
            )
        n = len(entries)
        return MoodStats(
            days=days,
            avg_stress=round(sum(e.stress for e in entries) / n, 1),
            avg_confidence=round(sum(e.confidence for e in entries) / n, 1),
            avg_motivation=round(sum(e.motivation for e in entries) / n, 1),
            avg_happiness=round(sum(e.happiness for e in entries) / n, 1),
            recent=[MoodResponse.model_validate(e) for e in entries[:days]],
        )
