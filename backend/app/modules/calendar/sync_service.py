"""
CalendarSyncService — reusable scheduling infrastructure.

Any module that owns a schedulable entity (Running races, Routines expand
on calendar list reads, and later Tasks, Study Planner, Travel, etc.) can
mirror it into the shared Calendar through a stable ``(source_module, source_id)``
key — or, for recurring day templates, expand live via ``RoutineService``.

This keeps a single source of truth, avoids duplicate events, and gives future
modules a one-line integration path instead of bespoke Running-specific logic.

Integration contract for a source module:
  * On create/update of the entity -> ``upsert_from_source(...)``
  * On delete of the entity        -> ``delete_from_source(...)``
  * The Calendar mirrors changes back to the source (reverse propagation) via
    ``CalendarService`` when a linked event is edited/deleted directly.

All writes happen at the repository level (no cross-service calls), so forward
and reverse sync can never loop.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.models import CalendarEvent


class CalendarSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_source(
        self, user_id: str, source_module: str, source_id: str
    ) -> CalendarEvent | None:
        result = await self.db.execute(
            select(CalendarEvent).where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.source_module == source_module,
                CalendarEvent.source_id == source_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_from_source(
        self,
        *,
        user_id: str,
        source_module: str,
        source_id: str,
        title: str,
        starts_at: datetime,
        ends_at: datetime | None = None,
        all_day: bool = False,
        category: str = "personal",
        location: str | None = None,
        description: str | None = None,
    ) -> CalendarEvent:
        """Create or update the single calendar event linked to this source."""
        event = await self.get_by_source(user_id, source_module, source_id)
        if event is None:
            event = CalendarEvent(
                user_id=user_id,
                source_module=source_module,
                source_id=source_id,
            )
            self.db.add(event)

        event.title = title
        event.starts_at = starts_at
        event.ends_at = ends_at
        event.all_day = all_day
        event.category = category
        event.location = location
        if description is not None:
            event.description = description

        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def delete_from_source(
        self, user_id: str, source_module: str, source_id: str
    ) -> None:
        """Remove the calendar event linked to this source, if any."""
        event = await self.get_by_source(user_id, source_module, source_id)
        if event is not None:
            await self.db.delete(event)
            await self.db.flush()
