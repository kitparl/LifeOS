from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import CALENDAR_EVENT_CREATED, EntityCreated, event_bus
from app.modules.calendar.models import CalendarEvent
from app.modules.calendar.repository import CalendarRepository
from app.modules.calendar.schemas import EventCreate, EventListItem, EventResponse, EventUpdate

# Modules whose calendar events mirror an owning entity. Editing/deleting such an
# event from the Calendar propagates back to the source (two-way sync).
_RUNNING_SOURCE = "running"


def _sort_key(dt: datetime) -> datetime:
    """Coerce naive datetimes (e.g. from SQLite) to UTC-aware so mixed lists sort safely."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _expand_recurring_event(
    event: CalendarEvent, start: datetime, end: datetime
) -> list[EventListItem]:
    """Expand a single recurring template into occurrences overlapping [start, end).

    Yearly Feb 29 anchors land on Feb 28 in non-leap years.
    """
    if not event.recurrence or event.recurrence == "none":
        return [EventListItem.model_validate(event)]

    duration = None
    if event.ends_at is not None:
        duration = event.ends_at - event.starts_at

    items: list[EventListItem] = []
    # Walk from a few days before the window so weekly/monthly anchors aren't missed.
    cursor_date = (start - timedelta(days=1)).date()
    last_date = (end + timedelta(days=1)).date()
    anchor = event.starts_at
    event_kind = getattr(event, "event_kind", None) or "normal"

    while cursor_date <= last_date:
        include = False
        if event.recurrence == "daily":
            include = True
        elif event.recurrence == "weekly":
            include = cursor_date.weekday() == anchor.weekday()
        elif event.recurrence == "monthly":
            include = cursor_date.day == anchor.day
        elif event.recurrence == "yearly":
            # Same month/day; Feb 29 → Feb 28 in non-leap years
            target_month = anchor.month
            target_day = anchor.day
            if target_month == 2 and target_day == 29:
                try:
                    include = cursor_date.month == 2 and cursor_date.day == 29
                except ValueError:
                    include = False
                if not include and cursor_date.month == 2 and cursor_date.day == 28:
                    # Non-leap year substitute
                    try:
                        date(cursor_date.year, 2, 29)
                        include = False  # leap year — wait for actual 29th
                    except ValueError:
                        include = True
            else:
                include = cursor_date.month == target_month and cursor_date.day == target_day

        if include and cursor_date >= anchor.date():
            starts_at = datetime.combine(cursor_date, anchor.timetz())
            # SQLite often returns naive datetimes; align with the query window tz.
            if starts_at.tzinfo is None:
                tz = anchor.tzinfo or start.tzinfo or end.tzinfo
                if tz is not None:
                    starts_at = starts_at.replace(tzinfo=tz)
            ends_at = starts_at + duration if duration is not None else None
            if ends_at is not None and ends_at < start:
                cursor_date += timedelta(days=1)
                continue
            if starts_at > end:
                cursor_date += timedelta(days=1)
                continue
            items.append(
                EventListItem(
                    id=f"{event.id}:{cursor_date.isoformat()}" if event.recurrence != "none" else event.id,
                    title=event.title,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    all_day=event.all_day,
                    category=event.category,
                    recurrence=event.recurrence,
                    event_kind=event_kind,
                    location=event.location,
                    source_module=event.source_module,
                    source_id=event.source_id or event.id,
                )
            )
        cursor_date += timedelta(days=1)

    return items or [EventListItem.model_validate(event)]


class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CalendarRepository(db)

    async def list_events(
        self, user_id: str, start=None, end=None
    ) -> list[EventListItem]:
        events = await self.repo.list_events(user_id, start=start, end=end)
        items: list[EventListItem] = []
        if start is not None and end is not None:
            # Recurring templates: also fetch events that started before the window
            # but recur into it (repo filters by starts_at overlap; expand handles rest).
            for e in events:
                if e.recurrence and e.recurrence != "none":
                    items.extend(_expand_recurring_event(e, start, end))
                else:
                    items.append(EventListItem.model_validate(e))
            from app.modules.routines.service import RoutineService

            items.extend(await RoutineService(self.db).expand_for_calendar(user_id, start, end))
        else:
            items = [EventListItem.model_validate(e) for e in events]

        items.sort(key=lambda i: _sort_key(i.starts_at))
        return items

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
