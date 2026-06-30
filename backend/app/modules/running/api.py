from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.running.schemas import (
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
from app.modules.running.service import RunningService

router = APIRouter(prefix="/running", tags=["running"])


@router.get("/runs", response_model=list[RunListItem])
async def list_runs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RunningService(db).list_runs(user.id)


@router.post("/runs", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    data: RunCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RunningService(db).create_run(user.id, data)


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RunningService(db).get_run(user.id, run_id)


@router.patch("/runs/{run_id}", response_model=RunResponse)
async def update_run(
    run_id: str,
    data: RunUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RunningService(db).update_run(user.id, run_id, data)


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_run(
    run_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await RunningService(db).delete_run(user.id, run_id)


@router.get("/races", response_model=list[RaceResponse])
async def list_races(
    upcoming_only: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RunningService(db).list_races(user.id, upcoming_only=upcoming_only)


@router.post("/races", response_model=RaceResponse, status_code=status.HTTP_201_CREATED)
async def create_race(
    data: RaceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RunningService(db).create_race(user.id, data)


@router.get("/races/{race_id}", response_model=RaceResponse)
async def get_race(
    race_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RunningService(db).get_race(user.id, race_id)


@router.patch("/races/{race_id}", response_model=RaceResponse)
async def update_race(
    race_id: str,
    data: RaceUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RunningService(db).update_race(user.id, race_id, data)


@router.delete("/races/{race_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_race(
    race_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await RunningService(db).delete_race(user.id, race_id)


@router.get("/settings", response_model=RunningSettingsResponse)
async def get_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RunningService(db).get_settings(user.id)


@router.patch("/settings", response_model=RunningSettingsResponse)
async def update_settings(
    data: RunningSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RunningService(db).update_settings(user.id, data)


@router.get("/stats", response_model=RunningStatsResponse)
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RunningService(db).get_stats(user.id)
