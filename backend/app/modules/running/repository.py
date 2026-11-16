
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import taxonomy
from app.core.pagination import Pagination, paginate
from app.core.timezone import utc_today
from app.modules.running.models import ORIGIN_MANUAL, RaceEvent, Run, RunningAccreditation, RunningSettings, RunningShoe
from app.modules.running.schemas import RaceCreate, RaceUpdate, RunCreate, RunningSettingsUpdate, RunUpdate


class RunningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_runs(self, user_id: str, shoe: str | None = None) -> list[Run]:
        """Fetch all runs (used for merge/stats); pagination happens in the service."""
        q = select(Run).where(Run.user_id == user_id)
        if shoe:
            q = q.where(Run.shoe == shoe)
        q = q.order_by(Run.run_date.desc(), Run.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def list_shoe_names(self, user_id: str) -> list[str]:
        return await taxonomy.list_names(self.db, RunningShoe, user_id)

    async def ensure_shoe(self, user_id: str, name: str) -> None:
        """Register a name for reuse (idempotent, case-insensitive)."""
        await taxonomy.ensure_name(self.db, RunningShoe, user_id, name)

    async def list_accreditation_names(self, user_id: str) -> list[str]:
        return await taxonomy.list_names(self.db, RunningAccreditation, user_id)

    async def ensure_accreditations(self, user_id: str, names: list[str]) -> list[str]:
        """Normalize (trim, de-dupe case-insensitively) and register each name for reuse."""
        clean = taxonomy.merge_names(names)
        for name in clean:
            await taxonomy.ensure_name(self.db, RunningAccreditation, user_id, name)
        return clean

    async def get_run(self, user_id: str, run_id: str) -> Run | None:
        result = await self.db.execute(select(Run).where(Run.id == run_id, Run.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_run(self, user_id: str, data: RunCreate) -> Run:
        shoe = (data.shoe or "").strip() or None
        run = Run(
            user_id=user_id,
            run_date=data.run_date,
            distance_km=data.distance_km,
            duration_seconds=data.duration_seconds,
            weather=data.weather,
            location=data.location,
            shoe=shoe,
            notes=data.notes,
        )
        self.db.add(run)
        if shoe:
            await self.ensure_shoe(user_id, shoe)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def update_run(self, run: Run, data: RunUpdate, locked: frozenset[str] = frozenset()) -> Run:
        """Apply the fields the caller sent, except `locked` ones (synced values the user cannot edit)."""
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if k not in locked}
        if "shoe" in updates:
            shoe = (updates["shoe"] or "").strip() or None
            updates["shoe"] = shoe
            if shoe:
                await self.ensure_shoe(run.user_id, shoe)
        for key, value in updates.items():
            setattr(run, key, value)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def get_run_by_activity(self, user_id: str, activity_id: str) -> Run | None:
        result = await self.db.execute(select(Run).where(Run.user_id == user_id, Run.activity_id == activity_id))
        return result.scalars().first()

    async def list_runs_by_activity_ids(self, user_id: str, activity_ids: list[str]) -> list[Run]:
        if not activity_ids:
            return []
        result = await self.db.execute(select(Run).where(Run.user_id == user_id, Run.activity_id.in_(activity_ids)))
        return list(result.scalars().all())

    async def list_unlinked_runs_on(self, user_id: str, run_date: date) -> list[Run]:
        """Manual runs of one day that no activity is linked to yet (match candidates)."""
        result = await self.db.execute(
            select(Run).where(Run.user_id == user_id, Run.run_date == run_date, Run.activity_id.is_(None))
        )
        return list(result.scalars().all())

    async def list_synced_runs_between(self, user_id: str, start: date, end: date) -> list[Run]:
        result = await self.db.execute(
            select(Run).where(
                Run.user_id == user_id,
                Run.activity_id.is_not(None),
                Run.run_date >= start,
                Run.run_date <= end,
            )
        )
        return list(result.scalars().all())

    async def count_synced_runs(self, user_id: str) -> tuple[int, int]:
        """(runs created by an import, manual runs a synced activity was merged into)."""
        manual = func.coalesce(Run.origin, ORIGIN_MANUAL) == ORIGIN_MANUAL
        total = await self.db.scalar(
            select(func.count()).select_from(Run).where(Run.user_id == user_id, Run.activity_id.is_not(None))
        )
        merged = await self.db.scalar(
            select(func.count()).select_from(Run).where(Run.user_id == user_id, Run.activity_id.is_not(None), manual)
        )
        return (total or 0) - (merged or 0), merged or 0

    async def add_run(self, run: Run) -> Run:
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def save(self, entity: Run | RaceEvent) -> None:
        await self.db.flush()
        await self.db.refresh(entity)

    async def get_race_by_run(self, user_id: str, run_id: str) -> RaceEvent | None:
        result = await self.db.execute(
            select(RaceEvent).where(RaceEvent.user_id == user_id, RaceEvent.run_id == run_id)
        )
        return result.scalars().first()

    async def list_attached_races(self, user_id: str) -> list[RaceEvent]:
        result = await self.db.execute(
            select(RaceEvent).where(RaceEvent.user_id == user_id, RaceEvent.run_id.is_not(None))
        )
        return list(result.scalars().all())

    async def delete_run(self, run: Run) -> None:
        await self.db.delete(run)
        await self.db.flush()

    async def list_races(
        self,
        user_id: str,
        upcoming_only: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[RaceEvent], int]:
        q = select(RaceEvent).where(RaceEvent.user_id == user_id)
        if upcoming_only:

            today = utc_today()
            q = q.where(RaceEvent.race_date >= today)
        q = q.order_by(RaceEvent.race_date.desc())
        if limit is None:
            result = await self.db.execute(q)
            rows = list(result.scalars().all())
            return rows, len(rows)
        return await paginate(self.db, q, Pagination(limit=limit, offset=offset))

    async def get_race(self, user_id: str, race_id: str) -> RaceEvent | None:
        result = await self.db.execute(
            select(RaceEvent).where(RaceEvent.id == race_id, RaceEvent.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_race(self, user_id: str, data: RaceCreate) -> RaceEvent:
        shoe = (data.shoe or "").strip() or None
        skipped = bool(data.skipped)
        attended = (not skipped) and (data.attended or bool(data.finish_time_seconds))
        if attended:
            skipped = False
        accreditations = await self.ensure_accreditations(user_id, data.accreditations)
        race = RaceEvent(
            user_id=user_id,
            name=data.name,
            race_date=data.race_date,
            distance_type=data.distance_type,
            distance_km=data.distance_km,
            location=data.location,
            organizer=data.organizer,
            bib_number=data.bib_number,
            finish_time_seconds=None if skipped else data.finish_time_seconds,
            position=data.position,
            medal=data.medal,
            certificate_url=data.certificate_url,
            event_url=data.event_url,
            photos=data.photos or [],
            registered=data.registered,
            attended=attended,
            skipped=skipped,
            shoe=shoe,
            accreditations=accreditations,
            notes=data.notes,
        )
        self.db.add(race)
        if shoe:
            await self.ensure_shoe(user_id, shoe)
        await self.db.flush()
        await self.db.refresh(race)
        return race

    async def update_race(self, race: RaceEvent, data: RaceUpdate) -> RaceEvent:
        updates = data.model_dump(exclude_unset=True)
        if updates.get("finish_time_seconds") and not updates.get("skipped"):
            updates["attended"] = True
        if "shoe" in updates:
            shoe = (updates["shoe"] or "").strip() or None
            updates["shoe"] = shoe
            if shoe:
                await self.ensure_shoe(race.user_id, shoe)
        if "accreditations" in updates:
            updates["accreditations"] = await self.ensure_accreditations(
                race.user_id, updates["accreditations"] or []
            )

        skipped = updates.get("skipped", race.skipped)
        attended = updates.get("attended", race.attended)
        if skipped:
            updates["skipped"] = True
            updates["attended"] = False
        elif attended:
            updates["attended"] = True
            updates["skipped"] = False

        for key, value in updates.items():
            setattr(race, key, value)
        await self.db.flush()
        await self.db.refresh(race)
        return race

    async def delete_race(self, race: RaceEvent) -> None:
        await self.db.delete(race)
        await self.db.flush()

    async def get_settings(self, user_id: str) -> RunningSettings:
        result = await self.db.execute(select(RunningSettings).where(RunningSettings.user_id == user_id))
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = RunningSettings(user_id=user_id)
            self.db.add(settings)
            await self.db.flush()
            await self.db.refresh(settings)
        return settings

    async def update_settings(self, user_id: str, data: RunningSettingsUpdate) -> RunningSettings:
        settings = await self.get_settings(user_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(settings, key, value)
        await self.db.flush()
        await self.db.refresh(settings)
        return settings
