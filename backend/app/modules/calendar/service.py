from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import CALENDAR_EVENT_CREATED, EntityCreated, event_bus
from app.modules.calendar.models import CalendarEvent
from app.modules.calendar.repository import CalendarRepository
from app.modules.calendar.schemas import EventCreate, EventListItem, EventResponse, EventUpdate

# Modules whose calendar events mirror an owning entity. Editing/deleting such an
# event from the Calendar propagates back to the source (two-way sync).
_RUNNING_SOURCE = "running"


class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db
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
        when = event.starts_at.strftime("%Y-%m-%d %H:%M") if event.starts_at else None
        await event_bus.emit(
            self.db,
            EntityCreated(
                event_type=CALENDAR_EVENT_CREATED,
                user_id=user_id,
                entity_id=event.id,
                title=event.title,
                when=when,
                module="calendar",
            ),
        )
        return EventResponse.model_validate(event)

    async def update_event(self, user_id: str, event_id: str, data: EventUpdate) -> EventResponse:
        event = await self.repo.get_by_id(user_id, event_id)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        updated = await self.repo.update(event, data)
        await self._propagate_to_source(user_id, updated)
        return EventResponse.model_validate(updated)

    async def delete_event(self, user_id: str, event_id: str) -> None:
        event = await self.repo.get_by_id(user_id, event_id)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        await self._delete_source(user_id, event)
        await self.repo.delete(event)

    async def _propagate_to_source(self, user_id: str, event: CalendarEvent) -> None:
        """Reverse sync: mirror a linked event's edits back to its owning entity.

        Writes at the repository level so it can never loop with the forward
        (source -> calendar) sync.
        """
        if event.source_module != _RUNNING_SOURCE or not event.source_id:
            return
        from app.modules.running.repository import RunningRepository

        race = await RunningRepository(self.db).get_race(user_id, event.source_id)
        if race is None:
            return
        race.name = event.title
        race.race_date = event.starts_at.date()
        race.location = event.location
        await self.db.flush()

    async def _delete_source(self, user_id: str, event: CalendarEvent) -> None:
        """Reverse sync: deleting a linked event deletes its owning entity."""
        if event.source_module != _RUNNING_SOURCE or not event.source_id:
            return
        from app.modules.running.repository import RunningRepository

        repo = RunningRepository(self.db)
        race = await repo.get_race(user_id, event.source_id)
        if race is not None:
            await repo.delete_race(race)

    async def get_dashboard_preview(self, user_id: str) -> list[tuple[str, str, str]]:
        events = await self.repo.get_upcoming(user_id, limit=5)
        return [(e.id, e.title, e.starts_at) for e in events]
