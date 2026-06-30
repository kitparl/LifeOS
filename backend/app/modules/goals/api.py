from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.goals.schemas import (
    GoalCreate,
    GoalListItem,
    GoalResponse,
    GoalUpdate,
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
)
from app.modules.goals.service import GoalService

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=list[GoalListItem])
async def list_goals(
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GoalService(db).list_goals(user.id, category, status)


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    data: GoalCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GoalService(db).create_goal(user.id, data)


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GoalService(db).get_goal(user.id, goal_id)


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    data: GoalUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GoalService(db).update_goal(user.id, goal_id, data)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await GoalService(db).delete_goal(user.id, goal_id)


@router.post("/{goal_id}/archive", response_model=GoalResponse)
async def archive_goal(
    goal_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GoalService(db).archive_goal(user.id, goal_id)


@router.post("/{goal_id}/milestones", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def add_milestone(
    goal_id: str,
    data: MilestoneCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GoalService(db).add_milestone(user.id, goal_id, data)


@router.patch("/{goal_id}/milestones/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    goal_id: str,
    milestone_id: str,
    data: MilestoneUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GoalService(db).update_milestone(user.id, goal_id, milestone_id, data)


@router.delete("/{goal_id}/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone(
    goal_id: str,
    milestone_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await GoalService(db).delete_milestone(user.id, goal_id, milestone_id)
