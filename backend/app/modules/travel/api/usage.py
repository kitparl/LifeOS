from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.travel.schemas.usage import (
    MapsSettingsOut,
    MapsSettingsUpdate,
    PricingRow,
    PricingUpdate,
    UsageSummary,
)
from app.modules.travel.services.usage_service import UsageService

router = APIRouter(prefix="/usage")


@router.get("", response_model=UsageSummary)
async def usage_summary(
    month: str | None = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UsageService(db).month_summary(user.id, month)


@router.get("/settings", response_model=MapsSettingsOut)
async def get_usage_settings(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await UsageService(db).get_settings(user.id)


@router.put("/settings", response_model=MapsSettingsOut)
async def update_usage_settings(
    data: MapsSettingsUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await UsageService(db).update_settings(user.id, data)


@router.get("/pricing", response_model=list[PricingRow])
async def list_pricing(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await UsageService(db).list_pricing(user.id)


@router.put("/pricing", response_model=list[PricingRow])
async def update_pricing(
    data: PricingUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await UsageService(db).update_pricing(user.id, data)
