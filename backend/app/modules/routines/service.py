from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.schemas import EventListItem
from app.modules.routines.repository import RoutineRepository
from app.modules.routines.schemas import (
    LinkedHabitBrief,
    RoutineBlockResponse,
    RoutineCreate,
    RoutineListItem,
    RoutineResponse,
    RoutineUpdate,
)

ROUTINE_SOURCE_MODULE = "routine"


class RoutineService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RoutineRepository(db)

    @staticmethod
    def _resolve_tz(name: str) -> ZoneInfo:
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")

    def _to_list_item(self, routine) -> RoutineListItem:
        return RoutineListItem(
            id=routine.id,
            name=routine.name,
            days_of_week=routine.days_of_week,
            timezone=routine.timezone,
            start_date=getattr(routine, "start_date", None),
            end_date=getattr(routine, "end_date", None),
            is_active=routine.is_active,
            block_count=len(routine.blocks),
            updated_at=routine.updated_at,
        )

    def _block_response(self, block) -> RoutineBlockResponse:
        habits = list(getattr(block, "habits", None) or [])
        return RoutineBlockResponse(
            id=block.id,
            title=block.title,
            start_time=block.start_time,
            end_time=block.end_time,
            area=block.area,
            category=block.category,
            notes=block.notes,
            sort_order=block.sort_order,
            habit_ids=[h.id for h in habits],
            habits=[LinkedHabitBrief(id=h.id, name=h.name) for h in habits],
        )

    def _to_response(self, routine) -> RoutineResponse:
        return RoutineResponse(
            id=routine.id,
            name=routine.name,
            description=routine.description,
            days_of_week=routine.days_of_week,
            timezone=routine.timezone,
            start_date=getattr(routine, "start_date", None),
            end_date=getattr(routine, "end_date", None),
            skip_dates=list(getattr(routine, "skip_dates", []) or []),
            is_active=routine.is_active,
            blocks=[self._block_response(b) for b in routine.blocks],
            created_at=routine.created_at,
            updated_at=routine.updated_at,
        )

    async def list_routines(self, user_id: str, active_only: bool = False) -> list[RoutineListItem]:
        routines = await self.repo.list_routines(user_id, active_only=active_only)
        return [self._to_list_item(r) for r in routines]

    async def get_routine(self, user_id: str, routine_id: str) -> RoutineResponse:
        routine = await self.repo.get_by_id(user_id, routine_id)
        if routine is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
        return self._to_response(routine)

    async def get_by_block(self, user_id: str, block_id: str) -> RoutineResponse:
        routine = await self.repo.get_by_block_id(user_id, block_id)
        if routine is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine block not found")
        return self._to_response(routine)

    async def create_routine(self, user_id: str, data: RoutineCreate) -> RoutineResponse:
        routine = await self.repo.create(user_id, data)
        return self._to_response(routine)

    async def update_routine(self, user_id: str, routine_id: str, data: RoutineUpdate) -> RoutineResponse:
        routine = await self.repo.get_by_id(user_id, routine_id)
        if routine is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
        updated = await self.repo.update(routine, data)
        return self._to_response(updated)

    async def delete_routine(self, user_id: str, routine_id: str) -> None:
        routine = await self.repo.get_by_id(user_id, routine_id)
        if routine is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
        await self.repo.delete(routine)

    async def expand_for_calendar(
        self,
        user_id: str,
        start: datetime | None,
        end: datetime | None,
    ) -> list[EventListItem]:
        """Expand active routine blocks into calendar events for [start, end)."""
        if start is None or end is None:
            return []

        routines = await self.repo.list_routines(user_id, active_only=True)
        items: list[EventListItem] = []

        # Normalize range to dates in UTC for iteration bounds, then apply each routine's TZ.
        start_date = start.date() if isinstance(start, datetime) else start
        end_date = end.date() if isinstance(end, datetime) else end
        # Inclusive walk: FullCalendar end is exclusive; still cover each day we might need.
        day = start_date - timedelta(days=1)
        last = end_date + timedelta(days=1)

        while day <= last:
            weekday = day.weekday()  # Mon=0
            for routine in routines:
                if weekday not in routine.days_of_week:
                    continue
                start_bound = getattr(routine, "start_date", None)
                end_bound = getattr(routine, "end_date", None)
                if start_bound and day < start_bound:
                    continue
                if end_bound and day > end_bound:
                    continue
                skip_set = set(getattr(routine, "skip_dates", []) or [])
                if day.isoformat() in skip_set:
                    continue
                tz = self._resolve_tz(routine.timezone)
                for block in routine.blocks:
                    starts_at = datetime.combine(day, block.start_time, tzinfo=tz)
                    ends_at = datetime.combine(day, block.end_time, tzinfo=tz)
                    # Keep only occurrences overlapping the requested window
                    if ends_at < start or starts_at > end:
                        continue
                    items.append(
                        EventListItem(
                            id=f"routine:{routine.id}:{block.id}:{day.isoformat()}",
                            title=block.title,
                            starts_at=starts_at,
                            ends_at=ends_at,
                            all_day=False,
                            category=block.category,
                            recurrence="none",
                            event_kind="normal",
                            location=None,
                            source_module=ROUTINE_SOURCE_MODULE,
                            source_id=block.id,
                        )
                    )
            day += timedelta(days=1)

        return items

    async def today_preview(self, user_id: str, limit: int = 8) -> list[tuple[str, str, datetime, str]]:
        """Return today's routine blocks for dashboard (event_id, title, starts_at, routine_id)."""
        routines = await self.repo.list_routines(user_id, active_only=True)
        if not routines:
            return []

        # Use the first routine's timezone, else Asia/Kolkata, to define "today".
        tz = self._resolve_tz(routines[0].timezone if routines else "Asia/Kolkata")
        now = datetime.now(tz)
        start = datetime.combine(now.date(), datetime.min.time(), tzinfo=tz)
        end = start + timedelta(days=1)
        items = await self.expand_for_calendar(user_id, start, end)
        ordered = sorted(items, key=lambda i: i.starts_at)[:limit]
        out: list[tuple[str, str, datetime, str]] = []
        for i in ordered:
            # id format: routine:{routine_id}:{block_id}:{date}
            parts = i.id.split(":")
            routine_id = parts[1] if len(parts) >= 2 else ""
            out.append((i.id, i.title, i.starts_at, routine_id))
        return out
