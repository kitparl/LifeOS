from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.models import CalendarEvent
from app.modules.calendar.schemas import EventCreate, EventUpdate


class CalendarRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_events(
        self, user_id: str, start: datetime | None = None, end: datetime | None = None
    ) -> list[CalendarEvent]:
        q = select(CalendarEvent).where(CalendarEvent.user_id == user_id)
        if start is not None:
            q = q.where(CalendarEvent.starts_at >= start)
        if end is not None:
            q = q.where(CalendarEvent.starts_at <= end)
        q = q.order_by(CalendarEvent.starts_at.asc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_upcoming(self, user_id: str, limit: int = 5) -> list[CalendarEvent]:
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(CalendarEvent)
            .where(CalendarEvent.user_id == user_id, CalendarEvent.starts_at >= now)
            .order_by(CalendarEvent.starts_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, event_id: str) -> CalendarEvent | None:
        result = await self.db.execute(
            select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: EventCreate) -> CalendarEvent:
        event = CalendarEvent(
            user_id=user_id,
            title=data.title,
            description=data.description,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            all_day=data.all_day,
            category=data.category,
            recurrence=data.recurrence,
            location=data.location,
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def update(self, event: CalendarEvent, data: EventUpdate) -> CalendarEvent:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(event, key, value)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def delete(self, event: CalendarEvent) -> None:
        await self.db.delete(event)
        await self.db.flush()
