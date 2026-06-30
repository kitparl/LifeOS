from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.running.models import RaceEvent, Run, RunningSettings
from app.modules.running.schemas import RaceCreate, RaceUpdate, RunCreate, RunUpdate, RunningSettingsUpdate
from app.modules.running.stats import weekly_km


class RunningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_runs(self, user_id: str) -> list[Run]:
        result = await self.db.execute(
            select(Run).where(Run.user_id == user_id).order_by(Run.run_date.desc(), Run.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_run(self, user_id: str, run_id: str) -> Run | None:
        result = await self.db.execute(select(Run).where(Run.id == run_id, Run.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_run(self, user_id: str, data: RunCreate) -> Run:
        run = Run(
            user_id=user_id,
            run_date=data.run_date,
            distance_km=data.distance_km,
            duration_seconds=data.duration_seconds,
            weather=data.weather,
            notes=data.notes,
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def update_run(self, run: Run, data: RunUpdate) -> Run:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(run, key, value)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def delete_run(self, run: Run) -> None:
        await self.db.delete(run)
        await self.db.flush()

    async def list_races(self, user_id: str, upcoming_only: bool = False) -> list[RaceEvent]:
        q = select(RaceEvent).where(RaceEvent.user_id == user_id)
        if upcoming_only:
            from datetime import UTC, datetime

            today = datetime.now(UTC).date()
            q = q.where(RaceEvent.race_date >= today)
        q = q.order_by(RaceEvent.race_date.asc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_race(self, user_id: str, race_id: str) -> RaceEvent | None:
        result = await self.db.execute(
            select(RaceEvent).where(RaceEvent.id == race_id, RaceEvent.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_race(self, user_id: str, data: RaceCreate) -> RaceEvent:
        race = RaceEvent(
            user_id=user_id,
            name=data.name,
            race_date=data.race_date,
            distance_type=data.distance_type,
            distance_km=data.distance_km,
            location=data.location,
            registered=data.registered,
            notes=data.notes,
        )
        self.db.add(race)
        await self.db.flush()
        await self.db.refresh(race)
        return race

    async def update_race(self, race: RaceEvent, data: RaceUpdate) -> RaceEvent:
        for key, value in data.model_dump(exclude_unset=True).items():
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

    async def get_weekly_km(self, user_id: str) -> float:
        runs = await self.list_runs(user_id)
        return weekly_km(runs)
