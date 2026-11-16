import json
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import RACE_ADDED, EntityCreated, event_bus
from app.core.exceptions import BadRequestError, ConflictError, get_or_404
from app.core.taxonomy import merge_names
from app.core.timezone import start_of_day_utc, utc_now
from app.modules.calendar.sync_service import CalendarSyncService
from app.modules.running.contracts import RevertResult, SyncedRunInput, SyncRunResult
from app.modules.running.matching import MatchCandidate, find_match, local_run_date
from app.modules.running.models import ORIGIN_MANUAL, SUGGESTED_ACCREDITATIONS, SUGGESTED_SHOES, RaceEvent, Run
from app.modules.running.repository import RunningRepository
from app.modules.running.schemas import (
    ChartPoint,
    PersonalBest,
    RaceCreate,
    RaceResponse,
    RaceUpdate,
    RunCreate,
    RunListItem,
    RunningSettingsResponse,
    RunningSettingsUpdate,
    RunningStatsResponse,
    RunResponse,
    RunUpdate,
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

# Source-module key used for the reusable Calendar scheduling linkage.
RUNNING_SOURCE_MODULE = "running"

# A synced run can be attached to a race held within this many days of it.
RACE_ATTACH_WINDOW_DAYS = 3
# Fields of a synced run that come from the activity and cannot be edited by hand.
SYNCED_RUN_LOCKED_FIELDS = frozenset({"run_date", "distance_km", "duration_seconds"})


class RunningService:
    def __init__(self, db: AsyncSession):
        self.repo = RunningRepository(db)
        self.calendar_sync = CalendarSyncService(db)

    async def _sync_race_to_calendar(self, user_id: str, race: RaceEvent) -> None:
        """Mirror a race/competition into the shared Calendar (all-day event)."""
        starts_at = start_of_day_utc(race.race_date)
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
    def _normalize_str_list(values) -> list[str]:
        if values is None:
            return []
        if isinstance(values, list):
            return [str(v) for v in values]
        if isinstance(values, str):
            try:
                parsed = json.loads(values)
            except json.JSONDecodeError:
                return []
            if isinstance(parsed, list):
                return [str(v) for v in parsed]
        return []

    @staticmethod
    def _bool_field(race: RaceEvent, field: str, default: bool = False) -> bool:
        value = getattr(race, field, default)
        if value is None:
            return default
        return bool(value)

    @staticmethod
    def _to_race_response(race: RaceEvent, activity_id: str | None = None) -> RaceResponse:
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
            photos=RunningService._normalize_str_list(race.photos),
            registered=RunningService._bool_field(race, "registered"),
            attended=RunningService._bool_field(race, "attended"),
            skipped=RunningService._bool_field(race, "skipped"),
            shoe=getattr(race, "shoe", None),
            accreditations=RunningService._normalize_str_list(getattr(race, "accreditations", None)),
            notes=race.notes,
            created_at=race.created_at,
            updated_at=race.updated_at,
            run_id=getattr(race, "run_id", None),
            activity_id=activity_id,
        )

    def _to_list_item(self, run, race: RaceEvent | None = None) -> RunListItem:
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
            event_name=race.name if race else None,
            origin=run.origin or ORIGIN_MANUAL,
            activity_id=run.activity_id,
            race_id=race.id if race else None,
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

    def _to_run_response(self, run, race_id: str | None = None) -> RunResponse:
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
            origin=run.origin or ORIGIN_MANUAL,
            activity_id=run.activity_id,
            race_id=race_id,
            start_time_utc=run.start_time_utc,
            elapsed_seconds=run.elapsed_seconds,
        )

    async def _race_id_for_run(self, user_id: str, run_id: str) -> str | None:
        race = await self.repo.get_race_by_run(user_id, run_id)
        return race.id if race else None

    async def list_runs(
        self,
        user_id: str,
        shoe: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[RunListItem], int]:
        runs = await self.repo.list_runs(user_id, shoe=shoe)
        races, _ = await self.repo.list_races(user_id)
        # A race with an attached run is shown once, as that run carrying the race name.
        race_by_run = {race.run_id: race for race in races if race.run_id}
        items = [self._to_list_item(r, race_by_run.get(r.id)) for r in runs]
        for race in races:
            if race.run_id or not self._bool_field(race, "attended"):
                continue
            race_shoe = (getattr(race, "shoe", None) or "").strip() or None
            if shoe and race_shoe != shoe:
                continue
            items.append(self._race_to_list_item(race))
        items.sort(key=lambda item: (item.run_date, item.updated_at), reverse=True)
        total = len(items)
        return items[offset : offset + limit], total

    async def list_shoes(self, user_id: str) -> list[str]:
        stored = await self.repo.list_shoe_names(user_id)
        return merge_names(SUGGESTED_SHOES, stored)

    async def create_shoe(self, user_id: str, name: str) -> str:
        clean = name.strip()
        if not clean:
            raise BadRequestError("Shoe name required")
        await self.repo.ensure_shoe(user_id, clean)
        return clean

    async def list_accreditations(self, user_id: str) -> list[str]:
        stored = await self.repo.list_accreditation_names(user_id)
        return merge_names(SUGGESTED_ACCREDITATIONS, stored)

    async def create_accreditation(self, user_id: str, name: str) -> str:
        clean = name.strip()
        if not clean:
            raise BadRequestError("Accreditation name required")
        await self.repo.ensure_accreditations(user_id, [clean])
        return clean

    async def get_run(self, user_id: str, run_id: str) -> RunResponse:
        run = get_or_404(await self.repo.get_run(user_id, run_id), "Run not found")
        return self._to_run_response(run, await self._race_id_for_run(user_id, run.id))

    async def create_run(self, user_id: str, data: RunCreate) -> RunResponse:
        run = await self.repo.create_run(user_id, data)
        return self._to_run_response(run)

    async def update_run(self, user_id: str, run_id: str, data: RunUpdate) -> RunResponse:
        run = get_or_404(await self.repo.get_run(user_id, run_id), "Run not found")
        locked = SYNCED_RUN_LOCKED_FIELDS if run.activity_id else frozenset()
        updated = await self.repo.update_run(run, data, locked=locked)
        return self._to_run_response(updated, await self._race_id_for_run(user_id, updated.id))

    async def delete_run(self, user_id: str, run_id: str) -> None:
        run = get_or_404(await self.repo.get_run(user_id, run_id), "Run not found")
        race = await self.repo.get_race_by_run(user_id, run.id)
        if race is not None:
            await self._detach(user_id, race)
        await self.repo.delete_run(run)

    async def list_races(
        self,
        user_id: str,
        upcoming_only: bool = False,
        limit: int | None = 25,
        offset: int = 0,
    ) -> tuple[list[RaceResponse], int]:
        races, total = await self.repo.list_races(
            user_id, upcoming_only=upcoming_only, limit=limit, offset=offset
        )
        return [self._to_race_response(r) for r in races], total

    async def get_race(self, user_id: str, race_id: str) -> RaceResponse:
        race = get_or_404(await self.repo.get_race(user_id, race_id), "Race not found")
        return await self._race_response_with_activity(user_id, race)

    async def _race_response_with_activity(self, user_id: str, race: RaceEvent) -> RaceResponse:
        run = await self.repo.get_run(user_id, race.run_id) if race.run_id else None
        return self._to_race_response(race, run.activity_id if run else None)

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
        race = get_or_404(await self.repo.get_race(user_id, race_id), "Race not found")
        updated = await self.repo.update_race(race, data)
        await self._sync_race_to_calendar(user_id, updated)
        return self._to_race_response(updated)

    async def delete_race(self, user_id: str, race_id: str) -> None:
        race = get_or_404(await self.repo.get_race(user_id, race_id), "Race not found")
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
        races, _ = await self.repo.list_races(user_id)
        settings = await self.repo.get_settings(user_id)
        last_run = runs[0] if runs else None
        total_km = round(sum(r.distance_km for r in runs), 2)
        # Totals and bests count an attached race once, through its run; event stats use every race.
        counted_races = [race for race in races if not race.run_id]
        bests = [PersonalBest(**b) for b in compute_personal_bests(runs, counted_races)]
        event_stats = compute_event_stats(races)
        return RunningStatsResponse(
            weekly_km=weekly_km(runs),
            weekly_goal_km=settings.weekly_goal_km,
            total_runs=len(runs),
            total_km=total_km,
            last_run_date=last_run.run_date if last_run else None,
            personal_bests=bests,
            shoe_totals=[ShoeTotal(**s) for s in compute_shoe_totals(runs, counted_races)],
            distance_over_time=[ChartPoint(**p) for p in compute_distance_over_time(runs, counted_races)],
            weekly_totals=[ChartPoint(**p) for p in compute_weekly_totals(runs, counted_races)],
            **event_stats,
        )

    # --- Synced runs -------------------------------------------------------------------------

    @staticmethod
    def _apply_synced_values(run: Run, data: SyncedRunInput) -> None:
        run.distance_km = round(data.distance_m / 1000, 2)
        run.duration_seconds = round(data.timer_seconds)
        run.elapsed_seconds = round(data.elapsed_seconds)
        run.start_time_utc = data.start_time_utc
        run.activity_id = data.activity_id
        run.synced_at = utc_now()

    async def sync_run_from_activity(self, user_id: str, data: SyncedRunInput) -> SyncRunResult:
        """Create a run for a synced activity, or merge it into the manual run it matches.

        Safe to call again for the same activity: the existing run is updated, never duplicated.
        """
        if data.distance_m <= 0 or data.timer_seconds <= 0:
            return SyncRunResult(run_id=None, created=False, matched_manual=False)

        existing = await self.repo.get_run_by_activity(user_id, data.activity_id)
        if existing is not None:
            self._apply_synced_values(existing, data)
            await self.repo.save(existing)
            is_manual = (existing.origin or ORIGIN_MANUAL) == ORIGIN_MANUAL
            return SyncRunResult(run_id=existing.id, created=False, matched_manual=is_manual)

        run_date = local_run_date(data.start_time_utc, data.timezone)
        unlinked = await self.repo.list_unlinked_runs_on(user_id, run_date)
        candidates = [MatchCandidate(r.id, r.distance_km, r.created_at) for r in unlinked]
        matched_id = find_match(data.distance_m / 1000, candidates)
        if matched_id is not None:
            run = next(r for r in unlinked if r.id == matched_id)
            # Keep what the user typed so the merge can be undone and AI/search keep showing it.
            if run.manual_distance_km is None:
                run.manual_distance_km = run.distance_km
            if run.manual_duration_seconds is None:
                run.manual_duration_seconds = run.duration_seconds
            self._apply_synced_values(run, data)
            await self.repo.save(run)
            return SyncRunResult(run_id=run.id, created=False, matched_manual=True)

        run = Run(user_id=user_id, run_date=run_date, origin=data.source, distance_km=0.0, duration_seconds=0)
        self._apply_synced_values(run, data)
        await self.repo.add_run(run)
        return SyncRunResult(run_id=run.id, created=True, matched_manual=False)

    async def revert_runs_for_activities(self, user_id: str, activity_ids: list[str]) -> RevertResult:
        """Undo syncing for activities that are being deleted.

        Import-created runs are deleted; runs the user logged by hand get their typed values back.
        """
        deleted = restored = detached = 0
        for run in await self.repo.list_runs_by_activity_ids(user_id, activity_ids):
            race = await self.repo.get_race_by_run(user_id, run.id)
            if race is not None:
                await self._detach(user_id, race)
                detached += 1
            if (run.origin or ORIGIN_MANUAL) != ORIGIN_MANUAL:
                await self.repo.delete_run(run)
                deleted += 1
                continue
            if run.manual_distance_km is not None:
                run.distance_km = run.manual_distance_km
            if run.manual_duration_seconds is not None:
                run.duration_seconds = run.manual_duration_seconds
            run.activity_id = None
            run.start_time_utc = None
            run.elapsed_seconds = None
            run.manual_distance_km = None
            run.manual_duration_seconds = None
            run.synced_at = None
            await self.repo.save(run)
            restored += 1
        return RevertResult(runs_deleted=deleted, runs_restored=restored, races_detached=detached)

    async def count_synced_runs(self, user_id: str) -> tuple[int, int]:
        return await self.repo.count_synced_runs(user_id)

    # --- Race attachment ---------------------------------------------------------------------

    async def list_race_candidates(self, user_id: str, race_id: str) -> list[RunListItem]:
        """Synced runs near the race date that are free to attach, closest first."""
        race = get_or_404(await self.repo.get_race(user_id, race_id), "Race not found")
        window = timedelta(days=RACE_ATTACH_WINDOW_DAYS)
        runs = await self.repo.list_synced_runs_between(user_id, race.race_date - window, race.race_date + window)
        taken = {r.run_id for r in await self.repo.list_attached_races(user_id) if r.id != race.id}
        race_km = _race_distance_km(race)
        free = [r for r in runs if r.id not in taken]
        free.sort(
            key=lambda r: (
                abs((r.run_date - race.race_date).days),
                abs(r.distance_km - race_km) if race_km else 0.0,
                -r.updated_at.timestamp(),
            )
        )
        return [self._to_list_item(r, race if race.run_id == r.id else None) for r in free]

    async def _detach(self, user_id: str, race: RaceEvent) -> None:
        """Restore the race to what it was before a run was attached."""
        if not race.run_id:
            return
        race.finish_time_seconds = race.finish_time_before_attach
        race.attended = bool(race.attended_before_attach)
        race.run_id = None
        race.finish_time_before_attach = None
        race.attended_before_attach = None
        await self.repo.save(race)

    async def attach_run_to_race(self, user_id: str, race_id: str, run_id: str) -> RaceResponse:
        race = get_or_404(await self.repo.get_race(user_id, race_id), "Race not found")
        run = get_or_404(await self.repo.get_run(user_id, run_id), "Run not found")
        if not run.activity_id:
            raise BadRequestError("Only a synced run can be attached to a race")
        other = await self.repo.get_race_by_run(user_id, run.id)
        if other is not None and other.id != race.id:
            raise ConflictError("This run is already attached to another race")
        if race.run_id == run.id:
            return self._to_race_response(race, run.activity_id)

        await self._detach(user_id, race)
        race.finish_time_before_attach = race.finish_time_seconds
        race.attended_before_attach = self._bool_field(race, "attended")
        race.run_id = run.id
        race.finish_time_seconds = run.elapsed_seconds or run.duration_seconds
        race.attended = True
        race.skipped = False
        await self.repo.save(race)
        await self._sync_race_to_calendar(user_id, race)
        return self._to_race_response(race, run.activity_id)

    async def detach_run_from_race(self, user_id: str, race_id: str) -> RaceResponse:
        race = get_or_404(await self.repo.get_race(user_id, race_id), "Race not found")
        await self._detach(user_id, race)
        return self._to_race_response(race)
