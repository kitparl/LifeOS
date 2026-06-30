from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.life_timeline.schemas import (
    LifeTimelineItem,
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
)
from app.modules.life_timeline.service import LifeTimelineService

router = APIRouter(prefix="/life-timeline", tags=["life-timeline"])


@router.get("", response_model=list[LifeTimelineItem])
async def complete_life_timeline(
    limit: int = Query(default=150, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LifeTimelineService(db).list_complete(user.id, limit)


@router.get("/milestones", response_model=list[MilestoneResponse])
async def list_milestones(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LifeTimelineService(db).list_milestones(user.id)


@router.post("/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    data: MilestoneCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LifeTimelineService(db).create_milestone(user.id, data)


@router.patch("/milestones/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    milestone_id: str,
    data: MilestoneUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LifeTimelineService(db).update_milestone(user.id, milestone_id, data)


@router.delete("/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone(
    milestone_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await LifeTimelineService(db).delete_milestone(user.id, milestone_id)
