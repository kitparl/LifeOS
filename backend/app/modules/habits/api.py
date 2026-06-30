from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.habits.schemas import HabitCreate, HabitListItem, HabitResponse, HabitUpdate
from app.modules.habits.service import HabitService

router = APIRouter(prefix="/habits", tags=["habits"])


@router.get("", response_model=list[HabitListItem])
async def list_habits(
    active_only: bool = Query(default=True),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HabitService(db).list_habits(user.id, active_only=active_only)


@router.post("", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
async def create_habit(
    data: HabitCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HabitService(db).create_habit(user.id, data)


@router.get("/{habit_id}", response_model=HabitResponse)
async def get_habit(
    habit_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HabitService(db).get_habit(user.id, habit_id)


@router.patch("/{habit_id}", response_model=HabitResponse)
async def update_habit(
    habit_id: str,
    data: HabitUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HabitService(db).update_habit(user.id, habit_id, data)


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(
    habit_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await HabitService(db).delete_habit(user.id, habit_id)


@router.post("/{habit_id}/complete", response_model=HabitResponse)
async def complete_habit_today(
    habit_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HabitService(db).complete_today(user.id, habit_id)


@router.delete("/{habit_id}/complete/today", response_model=HabitResponse)
async def uncomplete_habit_today(
    habit_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await HabitService(db).uncomplete_today(user.id, habit_id)
