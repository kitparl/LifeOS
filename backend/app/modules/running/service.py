import json
from datetime import datetime, time, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import RACE_ADDED, EntityCreated, event_bus
from app.modules.calendar.sync_service import CalendarSyncService
from app.modules.running.models import RaceEvent, SUGGESTED_SHOES
from app.modules.running.repository import RunningRepository

# Source-module key used for the reusable Calendar scheduling linkage.
RUNNING_SOURCE_MODULE = "running"
from app.modules.running.schemas import (
    ChartPoint,
    PersonalBest,
    RaceCreate,
    RaceResponse,
    RaceUpdate,
    RunCreate,
    RunListItem,
    RunResponse,
    RunUpdate,
    RunningSettingsResponse,
    RunningSettingsUpdate,
    RunningStatsResponse,
    ShoeTotal,
)
from app.modules.running.stats import (
    _race_distance_km,
    compute_distance_over_time,
    compute_event_stats,
    compute_pace,
    compute_personal_bests,
    compute_shoe_totals,
    compute_weekly_totals,
    weekly_km,
)


class RunningService:
    def __init__(self, db: AsyncSession):
        self.repo = RunningRepository(db)
        self.calendar_sync = CalendarSyncService(db)

    async def _sync_race_to_calendar(self, user_id: str, race: RaceEvent) -> None:
        """Mirror a race/competition into the shared Calendar (all-day event)."""
        starts_at = datetime.combine(race.race_date, time.min, tzinfo=timezone.utc)
        await self.calendar_sync.upsert_from_source(
            user_id=user_id,
            source_module=RUNNING_SOURCE_MODULE,
            source_id=race.id,
            title=race.name,
            starts_at=starts_at,
            all_day=True,
            category="running",
            location=race.location,
        )

    @staticmethod
    def _normalize_photos(photos) -> list[str]:
        if photos is None:
            return []
        if isinstance(photos, list):
            return [str(p) for p in photos]
        if isinstance(photos, str):
            try:
                parsed = json.loads(photos)
            except json.JSONDecodeError:
                return []
            if isinstance(parsed, list):
                return [str(p) for p in parsed]
        return []

    @staticmethod
    def _bool_field(race: RaceEvent, field: str, default: bool = False) -> bool:
        value = getattr(race, field, default)
        if value is None:
            return default
        return bool(value)

    @staticmethod
    def _to_race_response(race: RaceEvent) -> RaceResponse:
        return RaceResponse(
            id=race.id,
            name=race.name,
            race_date=race.race_date,
            distance_type=race.distance_type,
            distance_km=race.distance_km,
            location=race.location,
            organizer=race.organizer,
            bib_number=race.bib_number,
            finish_time_seconds=race.finish_time_seconds,
            position=race.position,
            medal=RunningService._bool_field(race, "medal"),
            certificate_url=race.certificate_url,
            event_url=race.event_url,
            photos=RunningService._normalize_photos(race.photos),
            registered=RunningService._bool_field(race, "registered"),
            attended=RunningService._bool_field(race, "attended"),
            skipped=RunningService._bool_field(race, "skipped"),
            shoe=getattr(race, "shoe", None),
            notes=race.notes,
            created_at=race.created_at,
            updated_at=race.updated_at,
        )

    def _to_list_item(self, run) -> RunListItem:
        return RunListItem(
            id=run.id,
            run_date=run.run_date,
            distance_km=run.distance_km,
            duration_seconds=run.duration_seconds,
            pace_min_per_km=compute_pace(run.distance_km, run.duration_seconds),
            weather=run.weather,
            location=getattr(run, 'location', None),
            shoe=getattr(run, 'shoe', None),
            updated_at=run.updated_at,
            source="run",
            event_name=None,
        )

    def _race_to_list_item(self, race: RaceEvent) -> RunListItem:
        distance_km = _race_distance_km(race)
        duration = race.finish_time_seconds or 0
        return RunListItem(
            id=race.id,
            run_date=race.race_date,
            distance_km=distance_km,
            duration_seconds=duration,
            pace_min_per_km=compute_pace(distance_km, duration) if duration and distance_km else 0.0,
            weather=None,
            location=race.location,
            shoe=getattr(race, "shoe", None),
            updated_at=race.updated_at,
            source="race",
            event_name=race.name,
        )

    def _to_run_response(self, run) -> RunResponse:
        return RunResponse(
            id=run.id,
            run_date=run.run_date,
            distance_km=run.distance_km,
            duration_seconds=run.duration_seconds,
            pace_min_per_km=compute_pace(run.distance_km, run.duration_seconds),
            weather=run.weather,
            location=getattr(run, 'location', None),
            shoe=getattr(run, 'shoe', None),
            notes=run.notes,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    async def list_runs(self, user_id: str, shoe: str | None = None) -> list[RunListItem]:
        runs = await self.repo.list_runs(user_id, shoe=shoe)
        items = [self._to_list_item(r) for r in runs]
        races = await self.repo.list_races(user_id)
        for race in races:
            if not self._bool_field(race, "attended"):
                continue
            race_shoe = (getattr(race, "shoe", None) or "").strip() or None
            if shoe and race_shoe != shoe:
                continue
            items.append(self._race_to_list_item(race))
        items.sort(key=lambda item: (item.run_date, item.updated_at), reverse=True)
        return items

    async def list_shoes(self, user_id: str) -> list[str]:
        stored = await self.repo.list_shoe_names(user_id)
        seen: dict[str, str] = {}
        for name in [*SUGGESTED_SHOES, *stored]:
            key = name.strip().lower()
            if key and key not in seen:
                seen[key] = name.strip()
        return sorted(seen.values(), key=str.lower)

    async def create_shoe(self, user_id: str, name: str) -> str:
        clean = name.strip()
        if not clean:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shoe name required")
        await self.repo.ensure_shoe(user_id, clean)
        return clean

    async def get_run(self, user_id: str, run_id: str) -> RunResponse:
        run = await self.repo.get_run(user_id, run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        return self._to_run_response(run)

    async def create_run(self, user_id: str, data: RunCreate) -> RunResponse:
        run = await self.repo.create_run(user_id, data)
        return self._to_run_response(run)

    async def update_run(self, user_id: str, run_id: str, data: RunUpdate) -> RunResponse:
        run = await self.repo.get_run(user_id, run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        updated = await self.repo.update_run(run, data)
        return self._to_run_response(updated)

    async def delete_run(self, user_id: str, run_id: str) -> None:
        run = await self.repo.get_run(user_id, run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        await self.repo.delete_run(run)

    async def list_races(self, user_id: str, upcoming_only: bool = False) -> list[RaceResponse]:
        races = await self.repo.list_races(user_id, upcoming_only=upcoming_only)
        return [self._to_race_response(r) for r in races]

    async def get_race(self, user_id: str, race_id: str) -> RaceResponse:
        race = await self.repo.get_race(user_id, race_id)
        if race is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
        return self._to_race_response(race)

    async def create_race(self, user_id: str, data: RaceCreate) -> RaceResponse:
        race = await self.repo.create_race(user_id, data)
        await self._sync_race_to_calendar(user_id, race)
        await event_bus.emit(
            self.repo.db,
            EntityCreated(
                event_type=RACE_ADDED,
                user_id=user_id,
                entity_id=race.id,
                title=race.name,
                when=race.race_date.isoformat() if race.race_date else None,
                module="running",
            ),
        )
        return self._to_race_response(race)

    async def update_race(self, user_id: str, race_id: str, data: RaceUpdate) -> RaceResponse:
        race = await self.repo.get_race(user_id, race_id)
        if race is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
        updated = await self.repo.update_race(race, data)
        await self._sync_race_to_calendar(user_id, updated)
        return self._to_race_response(updated)

    async def delete_race(self, user_id: str, race_id: str) -> None:
        race = await self.repo.get_race(user_id, race_id)
        if race is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
        await self.calendar_sync.delete_from_source(user_id, RUNNING_SOURCE_MODULE, race_id)
        await self.repo.delete_race(race)

    async def get_settings(self, user_id: str) -> RunningSettingsResponse:
        settings = await self.repo.get_settings(user_id)
        return RunningSettingsResponse.model_validate(settings)

    async def update_settings(self, user_id: str, data: RunningSettingsUpdate) -> RunningSettingsResponse:
        settings = await self.repo.update_settings(user_id, data)
        return RunningSettingsResponse.model_validate(settings)

    async def get_stats(self, user_id: str) -> RunningStatsResponse:
        runs = await self.repo.list_runs(user_id)
        races = await self.repo.list_races(user_id)
        settings = await self.repo.get_settings(user_id)
        last_run = runs[0] if runs else None
        total_km = round(sum(r.distance_km for r in runs), 2)
        bests = [PersonalBest(**b) for b in compute_personal_bests(runs, races)]
        event_stats = compute_event_stats(races)
        return RunningStatsResponse(
            weekly_km=weekly_km(runs),
            weekly_goal_km=settings.weekly_goal_km,
            total_runs=len(runs),
            total_km=total_km,
            last_run_date=last_run.run_date if last_run else None,
            personal_bests=bests,
            shoe_totals=[ShoeTotal(**s) for s in compute_shoe_totals(runs, races)],
            distance_over_time=[ChartPoint(**p) for p in compute_distance_over_time(runs, races)],
            weekly_totals=[ChartPoint(**p) for p in compute_weekly_totals(runs, races)],
            **event_stats,
        )

    async def get_dashboard_progress(self, user_id: str) -> dict | None:
        runs = await self.repo.list_runs(user_id)
        if not runs:
            return None
        settings = await self.repo.get_settings(user_id)
        last = runs[0]
        return {
            "weekly_km": weekly_km(runs),
            "goal_km": settings.weekly_goal_km,
            "last_run": last.run_date.isoformat(),
        }
