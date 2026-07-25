from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.habits.models import Habit
from app.modules.routines.models import Routine, RoutineBlock
from app.modules.routines.schemas import RoutineBlockCreate, RoutineCreate, RoutineUpdate


class RoutineRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_routines(self, user_id: str, active_only: bool = False) -> list[Routine]:
        q = (
            select(Routine)
            .where(Routine.user_id == user_id)
            .options(selectinload(Routine.blocks).selectinload(RoutineBlock.habits))
            .order_by(Routine.name.asc())
        )
        if active_only:
            q = q.where(Routine.is_active.is_(True))
        result = await self.db.execute(q)
        return list(result.scalars().unique().all())

    async def get_by_id(self, user_id: str, routine_id: str) -> Routine | None:
        result = await self.db.execute(
            select(Routine)
            .where(Routine.id == routine_id, Routine.user_id == user_id)
            .options(selectinload(Routine.blocks).selectinload(RoutineBlock.habits))
        )
        return result.scalar_one_or_none()

    async def get_by_block_id(self, user_id: str, block_id: str) -> Routine | None:
        result = await self.db.execute(
            select(Routine)
            .join(RoutineBlock)
            .where(RoutineBlock.id == block_id, Routine.user_id == user_id)
            .options(selectinload(Routine.blocks).selectinload(RoutineBlock.habits))
        )
        return result.scalar_one_or_none()

    async def _resolve_habits(self, user_id: str, habit_ids: list[str]) -> list[Habit]:
        if not habit_ids:
            return []
        unique = list(dict.fromkeys(habit_ids))
        result = await self.db.execute(
            select(Habit).where(Habit.user_id == user_id, Habit.id.in_(unique))
        )
        found = {h.id: h for h in result.scalars().all()}
        return [found[hid] for hid in unique if hid in found]

    async def _make_blocks(self, user_id: str, blocks: list[RoutineBlockCreate]) -> list[RoutineBlock]:
        out: list[RoutineBlock] = []
        for i, b in enumerate(blocks):
            block = RoutineBlock(
                title=b.title,
                start_time=b.start_time,
                end_time=b.end_time,
                area=b.area,
                category=b.category,
                notes=b.notes,
                sort_order=b.sort_order if b.sort_order else i,
            )
            block.habits = await self._resolve_habits(user_id, b.habit_ids or [])
            out.append(block)
        return out

    async def create(self, user_id: str, data: RoutineCreate) -> Routine:
        routine = Routine(
            user_id=user_id,
            name=data.name,
            description=data.description,
            timezone=data.timezone,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        routine.days_of_week = data.days_of_week
        routine.skip_dates = data.skip_dates or []
        routine.blocks = await self._make_blocks(user_id, data.blocks)
        self.db.add(routine)
        await self.db.flush()
        await self.db.refresh(routine, ["blocks"])
        return routine

    async def update(self, routine: Routine, data: RoutineUpdate) -> Routine:
        payload = data.model_dump(exclude_unset=True)
        blocks = payload.pop("blocks", None)
        days = payload.pop("days_of_week", None)
        skips = payload.pop("skip_dates", None)

        for key, value in payload.items():
            setattr(routine, key, value)
        if days is not None:
            routine.days_of_week = days
        if skips is not None:
            routine.skip_dates = skips
        if blocks is not None:
            routine.blocks.clear()
            await self.db.flush()
            routine.blocks = await self._make_blocks(routine.user_id, data.blocks or [])

        await self.db.flush()
        await self.db.refresh(routine, ["blocks"])
        return routine

    async def delete(self, routine: Routine) -> None:
        await self.db.delete(routine)
        await self.db.flush()
