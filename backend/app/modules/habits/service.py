from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.habits.repository import HabitRepository
from app.modules.habits.schemas import (
    HabitCreate,
    HabitListItem,
    HabitLogResponse,
    HabitResponse,
    HabitStats,
    HabitUpdate,
)
from app.modules.habits.stats import (
    calculate_completion_rate,
    calculate_streak,
    count_missed_periods,
    is_completed_for_period,
)


class HabitService:
    def __init__(self, db: AsyncSession):
        self.repo = HabitRepository(db)

    def _build_stats(self, habit) -> HabitStats:
        recent = sorted(habit.logs, key=lambda l: l.log_date, reverse=True)[:90]
        return HabitStats(
            streak=calculate_streak(habit),
            completion_rate=calculate_completion_rate(habit),
            total_logs=len(habit.logs),
            missed_periods=count_missed_periods(habit),
            recent_logs=[HabitLogResponse.model_validate(l) for l in recent],
        )

    def _to_list_item(self, habit) -> HabitListItem:
        return HabitListItem(
            id=habit.id,
            name=habit.name,
            frequency=habit.frequency,
            is_active=habit.is_active,
            completed_today=is_completed_for_period(habit),
            streak=calculate_streak(habit),
            completion_rate=calculate_completion_rate(habit),
            updated_at=habit.updated_at,
        )

    def _to_response(self, habit) -> HabitResponse:
        stats = self._build_stats(habit)
        return HabitResponse(
            id=habit.id,
            name=habit.name,
            description=habit.description,
            frequency=habit.frequency,
            is_active=habit.is_active,
            created_at=habit.created_at,
            updated_at=habit.updated_at,
            completed_today=is_completed_for_period(habit),
            streak=stats.streak,
            completion_rate=stats.completion_rate,
            stats=stats,
            logs=stats.recent_logs,
        )

    async def list_habits(self, user_id: str, active_only: bool = True) -> list[HabitListItem]:
        habits = await self.repo.list_habits(user_id, active_only=active_only)
        return [self._to_list_item(h) for h in habits]

    async def get_habit(self, user_id: str, habit_id: str) -> HabitResponse:
        habit = await self.repo.get_by_id(user_id, habit_id)
        if habit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        return self._to_response(habit)

    async def create_habit(self, user_id: str, data: HabitCreate) -> HabitResponse:
        habit = await self.repo.create(user_id, data)
        return self._to_response(habit)

    async def update_habit(self, user_id: str, habit_id: str, data: HabitUpdate) -> HabitResponse:
        habit = await self.repo.get_by_id(user_id, habit_id)
        if habit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        updated = await self.repo.update(habit, data)
        return self._to_response(updated)

    async def delete_habit(self, user_id: str, habit_id: str) -> None:
        habit = await self.repo.get_by_id(user_id, habit_id)
        if habit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        await self.repo.delete(habit)

    async def complete_today(self, user_id: str, habit_id: str) -> HabitResponse:
        habit = await self.repo.get_by_id(user_id, habit_id)
        if habit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        await self.repo.complete_today(habit)
        habit = await self.repo.get_by_id(user_id, habit_id)
        return self._to_response(habit)

    async def uncomplete_today(self, user_id: str, habit_id: str) -> HabitResponse:
        habit = await self.repo.get_by_id(user_id, habit_id)
        if habit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        await self.repo.uncomplete_today(habit)
        habit = await self.repo.get_by_id(user_id, habit_id)
        return self._to_response(habit)

    async def get_dashboard_items(self, user_id: str) -> list[tuple[str, str, bool]]:
        items = await self.repo.get_dashboard_habits(user_id)
        return [(h.id, h.name, completed) for h, completed in items]
