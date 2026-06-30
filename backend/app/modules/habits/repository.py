from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.habits.models import Habit, HabitLog
from app.modules.habits.schemas import HabitCreate, HabitUpdate
from app.modules.habits.stats import _today, is_completed_for_period


class HabitRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_habits(self, user_id: str, active_only: bool = True) -> list[Habit]:
        q = select(Habit).where(Habit.user_id == user_id).options(selectinload(Habit.logs))
        if active_only:
            q = q.where(Habit.is_active.is_(True))
        q = q.order_by(Habit.name.asc())
        result = await self.db.execute(q)
        return list(result.scalars().unique().all())

    async def get_by_id(self, user_id: str, habit_id: str) -> Habit | None:
        result = await self.db.execute(
            select(Habit)
            .where(Habit.id == habit_id, Habit.user_id == user_id)
            .options(selectinload(Habit.logs))
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: HabitCreate) -> Habit:
        habit = Habit(
            user_id=user_id,
            name=data.name,
            description=data.description,
            frequency=data.frequency,
        )
        self.db.add(habit)
        await self.db.flush()
        await self.db.refresh(habit, ["logs"])
        return habit

    async def update(self, habit: Habit, data: HabitUpdate) -> Habit:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(habit, key, value)
        await self.db.flush()
        await self.db.refresh(habit, ["logs"])
        return habit

    async def delete(self, habit: Habit) -> None:
        await self.db.delete(habit)
        await self.db.flush()

    async def complete_today(self, habit: Habit) -> HabitLog:
        today = _today()
        existing = next((log for log in habit.logs if log.log_date == today), None)
        if existing:
            return existing
        log = HabitLog(habit_id=habit.id, log_date=today)
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(habit, ["logs"])
        return log

    async def uncomplete_today(self, habit: Habit) -> None:
        today = _today()
        log = next((l for l in habit.logs if l.log_date == today), None)
        if log:
            await self.db.delete(log)
            await self.db.flush()
            await self.db.refresh(habit, ["logs"])

    async def get_dashboard_habits(self, user_id: str) -> list[tuple[Habit, bool]]:
        habits = await self.list_habits(user_id, active_only=True)
        return [(h, is_completed_for_period(h)) for h in habits]
