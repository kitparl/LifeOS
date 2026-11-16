from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.core.timezone import as_utc, start_of_day_utc
from app.modules.calendar.schemas import EventListItem
from app.modules.calendar.service import CalendarService
from app.modules.tasks.due_dates import noon_utc
from app.modules.timeline.repository import TimelineRepository
from app.modules.timeline.schemas import TimelineItem, TimelineSource
from app.modules.timeline.sources import CALENDAR_SOURCE_MODULE_MAP, TIMELINE_SOURCES

MAX_WINDOW_DAYS = 366
_SOURCE_KEYS = frozenset(s.key for s in TIMELINE_SOURCES)
# Sources whose items (fully or partly) arrive via the shared Calendar feed.
_CALENDAR_FED = frozenset({"calendar", "running", "travel", "routines"})


def _format_duration(seconds: int) -> str:
    hours, rem = divmod(seconds, 3600)
    minutes = rem // 60
    return f"{hours}h {minutes:02d}m" if hours else f"{minutes} min"


def _calendar_route(event: EventListItem, source: str) -> str:
    if source == "routines":
        # Routine expansions use ids "routine:{routineId}:{blockId}:{date}".
        parts = event.id.split(":")
        return f"/routines/{parts[1]}" if len(parts) > 1 else "/routines"
    if source == "running" and event.source_id:
        return f"/running/races/{event.source_id}"
    if source == "travel" and event.source_id:
        return f"/travel/trips/{event.source_id}"
    # Recurring occurrences are "{uuid}:{YYYY-MM-DD}"; the detail page wants the template id.
    return f"/calendar/{event.id[:36]}"


class TimelineService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TimelineRepository(db)

    @staticmethod
    def list_sources() -> list[TimelineSource]:
        return list(TIMELINE_SOURCES)

    async def list_items(
        self, user_id: str, start: date, end: date, sources: list[str] | None
    ) -> list[TimelineItem]:
        if end < start:
            raise BadRequestError("end must be on or after start")
        if (end - start).days > MAX_WINDOW_DAYS:
            raise BadRequestError(f"Window cannot exceed {MAX_WINDOW_DAYS} days")
        enabled = self._resolve_sources(sources)

        items: list[TimelineItem] = []
        if enabled & _CALENDAR_FED:
            items.extend(await self._calendar(user_id, start, end, enabled))
        if "tasks" in enabled:
            items.extend(await self._tasks(user_id, start, end))
        if "running" in enabled:
            items.extend(await self._runs(user_id, start, end))
        if "journal" in enabled:
            items.extend(await self._journal(user_id, start, end))
        if "finance" in enabled:
            items.extend(await self._loan_emis(user_id, start, end))
        if "wishlist" in enabled:
            items.extend(await self._wishlist(user_id, start, end))

        items.sort(key=lambda i: as_utc(i.starts_at))
        return items

    @staticmethod
    def _resolve_sources(sources: list[str] | None) -> set[str]:
        if not sources:
            return {s.key for s in TIMELINE_SOURCES if s.default_enabled}
        unknown = set(sources) - _SOURCE_KEYS
        if unknown:
            raise BadRequestError(f"Unknown timeline source(s): {', '.join(sorted(unknown))}")
        return set(sources)

    async def _calendar(
        self, user_id: str, start: date, end: date, enabled: set[str]
    ) -> list[TimelineItem]:
        events, _ = await CalendarService(self.db).list_events(
            user_id,
            start=start_of_day_utc(start),
            end=start_of_day_utc(end + timedelta(days=1)),
            limit=None,
        )
        items: list[TimelineItem] = []
        for e in events:
            source = CALENDAR_SOURCE_MODULE_MAP.get(e.source_module or "", "calendar")
            if source not in enabled:
                continue
            items.append(
                TimelineItem(
                    id=f"event:{e.id}",
                    source=source,
                    kind="event",
                    title=e.title,
                    subtitle=e.location,
                    starts_at=e.starts_at,
                    ends_at=e.ends_at,
                    all_day=e.all_day,
                    status=e.category,
                    route=_calendar_route(e, source),
                )
            )
        return items

    async def _tasks(self, user_id: str, start: date, end: date) -> list[TimelineItem]:
        tasks = await self.repo.tasks_due(
            user_id, start_of_day_utc(start), start_of_day_utc(end + timedelta(days=1))
        )
        return [
            TimelineItem(
                id=f"task:{t.id}",
                source="tasks",
                kind="task",
                title=t.title,
                subtitle=f"{t.priority.capitalize()} priority",
                starts_at=t.due_date,
                status=t.status,
                route=f"/tasks/{t.id}",
            )
            for t in tasks
        ]

    async def _runs(self, user_id: str, start: date, end: date) -> list[TimelineItem]:
        return [
            TimelineItem(
                id=f"run:{r.id}",
                source="running",
                kind="run",
                title=f"{r.distance_km:g} km run",
                subtitle=" · ".join(filter(None, [_format_duration(r.duration_seconds), r.location])),
                starts_at=noon_utc(r.run_date),
                all_day=True,
                route=f"/running/{r.id}",
            )
            for r in await self.repo.runs(user_id, start, end)
        ]

    async def _journal(self, user_id: str, start: date, end: date) -> list[TimelineItem]:
        return [
            TimelineItem(
                id=f"journal:{j.id}",
                source="journal",
                kind="journal",
                title=j.title or f"{j.entry_type.capitalize()} journal",
                subtitle=j.content[:140] or None,
                starts_at=noon_utc(j.entry_date),
                all_day=True,
                status=j.entry_type,
                route=f"/journal/{j.id}",
            )
            for j in await self.repo.journal_entries(user_id, start, end)
        ]

    async def _loan_emis(self, user_id: str, start: date, end: date) -> list[TimelineItem]:
        return [
            TimelineItem(
                id=f"emi:{emi.id}",
                source="finance",
                kind="emi",
                title=f"{loan.name} · EMI #{emi.emi_number}",
                subtitle=f"{emi.amount:,.2f}",
                starts_at=noon_utc(emi.due_date),
                all_day=True,
                status=emi.status.lower(),
                route="/finance",
            )
            for emi, loan in await self.repo.loan_emis(user_id, start, end)
        ]

    async def _wishlist(self, user_id: str, start: date, end: date) -> list[TimelineItem]:
        return [
            TimelineItem(
                id=f"wish:{w.id}",
                source="wishlist",
                kind="wish",
                title=w.title,
                subtitle="Achieved",
                starts_at=noon_utc(w.achieved_date),
                all_day=True,
                status=w.status,
                route=f"/wishlist/{w.id}",
            )
            for w in await self.repo.wishlist_achieved(user_id, start, end)
            if w.achieved_date is not None
        ]
