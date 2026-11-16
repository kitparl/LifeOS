from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.health.schemas import (
    HealthDayInput,
    HealthDayResponse,
    HealthRange,
    HealthTodayResponse,
    MeasurementCreate,
    MeasurementKind,
    MeasurementResponse,
    MetricInfo,
    MetricSeriesResponse,
    SleepResponse,
)
from app.modules.health.service import HealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/metrics", response_model=list[MetricInfo])
async def metric_catalogue(user: User = Depends(get_current_user)):
    return HealthService.metric_catalogue()


@router.get("/metrics/{key}", response_model=MetricSeriesResponse)
async def metric_series(
    key: str,
    range: HealthRange = Query(default="30d"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HealthService(db).get_metric_series(user.id, key, range)


@router.get("/today", response_model=HealthTodayResponse)
async def today(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await HealthService(db).get_today(user.id)


@router.get("/sleep", response_model=SleepResponse)
async def sleep(
    range: HealthRange = Query(default="30d"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HealthService(db).get_sleep(user.id, range)


@router.get("/days", response_model=list[HealthDayResponse])
async def list_days(
    start: date,
    end: date,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HealthService(db).get_days(user.id, start, end)


@router.get("/days/{day}", response_model=HealthDayResponse)
async def get_day(day: date, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await HealthService(db).get_day(user.id, day)


@router.put("/days/{day}", response_model=HealthDayResponse)
async def put_day(
    day: date,
    data: HealthDayInput,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HealthService(db).upsert_manual_day(user.id, day, data.values)


@router.get("/measurements", response_model=list[MeasurementResponse])
async def list_measurements(
    kind: MeasurementKind,
    start: date,
    end: date,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HealthService(db).list_measurements(user.id, kind, start, end)


@router.post("/measurements", response_model=MeasurementResponse, status_code=status.HTTP_201_CREATED)
async def add_measurement(
    data: MeasurementCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HealthService(db).add_measurement(user.id, data)


@router.delete("/measurements/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_measurement(
    measurement_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await HealthService(db).delete_measurement(user.id, measurement_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
