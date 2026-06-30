from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.repository import CalendarRepository
from app.modules.calendar.schemas import EventCreate, EventListItem, EventResponse, EventUpdate


class CalendarService:
    def __init__(self, db: AsyncSession):
        self.repo = CalendarRepository(db)

    async def list_events(
        self, user_id: str, start=None, end=None
    ) -> list[EventListItem]:
        events = await self.repo.list_events(user_id, start=start, end=end)
        return [EventListItem.model_validate(e) for e in events]

    async def get_event(self, user_id: str, event_id: str) -> EventResponse:
        event = await self.repo.get_by_id(user_id, event_id)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return EventResponse.model_validate(event)

    async def create_event(self, user_id: str, data: EventCreate) -> EventResponse:
        event = await self.repo.create(user_id, data)
        return EventResponse.model_validate(event)

    async def update_event(self, user_id: str, event_id: str, data: EventUpdate) -> EventResponse:
        event = await self.repo.get_by_id(user_id, event_id)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        updated = await self.repo.update(event, data)
        return EventResponse.model_validate(updated)

    async def delete_event(self, user_id: str, event_id: str) -> None:
        event = await self.repo.get_by_id(user_id, event_id)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        await self.repo.delete(event)

    async def get_dashboard_preview(self, user_id: str) -> list[tuple[str, str, str]]:
        events = await self.repo.get_upcoming(user_id, limit=5)
        return [(e.id, e.title, e.starts_at) for e in events]
