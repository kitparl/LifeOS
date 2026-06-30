from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.mood.schemas import MoodResponse, MoodStats, MoodUpsert
from app.modules.mood.service import MoodService

router = APIRouter(prefix="/mood", tags=["mood"])


@router.get("/entries", response_model=list[MoodResponse])
async def list_mood_entries(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MoodService(db).list_entries(user.id, days=days)


@router.get("/today", response_model=MoodResponse | None)
async def get_today_mood(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MoodService(db).get_today(user.id)


@router.put("/today", response_model=MoodResponse)
async def upsert_today_mood(
    data: MoodUpsert,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MoodService(db).upsert_today(user.id, data)


@router.get("/stats", response_model=MoodStats)
async def get_mood_stats(
    days: int = Query(default=7, ge=1, le=90),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MoodService(db).get_stats(user.id, days=days)
