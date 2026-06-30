from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.running.repository import RunningRepository
from app.modules.running.schemas import (
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
)
from app.modules.running.stats import compute_pace, compute_personal_bests, weekly_km


class RunningService:
    def __init__(self, db: AsyncSession):
        self.repo = RunningRepository(db)

    def _to_list_item(self, run) -> RunListItem:
        return RunListItem(
            id=run.id,
            run_date=run.run_date,
            distance_km=run.distance_km,
            duration_seconds=run.duration_seconds,
            pace_min_per_km=compute_pace(run.distance_km, run.duration_seconds),
            weather=run.weather,
            updated_at=run.updated_at,
        )

    def _to_run_response(self, run) -> RunResponse:
        return RunResponse(
            id=run.id,
            run_date=run.run_date,
            distance_km=run.distance_km,
            duration_seconds=run.duration_seconds,
            pace_min_per_km=compute_pace(run.distance_km, run.duration_seconds),
            weather=run.weather,
            notes=run.notes,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    async def list_runs(self, user_id: str) -> list[RunListItem]:
        runs = await self.repo.list_runs(user_id)
        return [self._to_list_item(r) for r in runs]

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
        return [RaceResponse.model_validate(r) for r in races]

    async def get_race(self, user_id: str, race_id: str) -> RaceResponse:
        race = await self.repo.get_race(user_id, race_id)
        if race is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
        return RaceResponse.model_validate(race)

    async def create_race(self, user_id: str, data: RaceCreate) -> RaceResponse:
        race = await self.repo.create_race(user_id, data)
        return RaceResponse.model_validate(race)

    async def update_race(self, user_id: str, race_id: str, data: RaceUpdate) -> RaceResponse:
        race = await self.repo.get_race(user_id, race_id)
        if race is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
        updated = await self.repo.update_race(race, data)
        return RaceResponse.model_validate(updated)

    async def delete_race(self, user_id: str, race_id: str) -> None:
        race = await self.repo.get_race(user_id, race_id)
        if race is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
        await self.repo.delete_race(race)

    async def get_settings(self, user_id: str) -> RunningSettingsResponse:
        settings = await self.repo.get_settings(user_id)
        return RunningSettingsResponse.model_validate(settings)

    async def update_settings(self, user_id: str, data: RunningSettingsUpdate) -> RunningSettingsResponse:
        settings = await self.repo.update_settings(user_id, data)
        return RunningSettingsResponse.model_validate(settings)

    async def get_stats(self, user_id: str) -> RunningStatsResponse:
        runs = await self.repo.list_runs(user_id)
        settings = await self.repo.get_settings(user_id)
        last_run = runs[0] if runs else None
        total_km = round(sum(r.distance_km for r in runs), 2)
        bests = [PersonalBest(**b) for b in compute_personal_bests(runs)]
        return RunningStatsResponse(
            weekly_km=weekly_km(runs),
            weekly_goal_km=settings.weekly_goal_km,
            total_runs=len(runs),
            total_km=total_km,
            last_run_date=last_run.run_date if last_run else None,
            personal_bests=bests,
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
