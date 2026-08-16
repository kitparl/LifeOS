from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.habits.models import Habit
from app.modules.routines.models import (
    Routine,
    RoutineAreaOption,
    RoutineBlock,
    RoutineCategoryOption,
)
from app.modules.routines.schemas import RoutineBlockCreate, RoutineCreate, RoutineUpdate


class RoutineRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_routines(self, user_id: str, active_only: bool = False) -> list[Routine]:
        q = (
            select(Routine)
            .where(Routine.user_id == user_id)
            .options(selectinload(Routine.blocks).selectinload(RoutineBlock.habits))
            .order_by(
                Routine.start_date.is_(None).asc(),
                Routine.start_date.desc(),
                Routine.end_date.is_(None).asc(),
                Routine.end_date.desc(),
                Routine.name.asc(),
            )
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

    async def _register_block_taxonomy(self, user_id: str, blocks: list[RoutineBlockCreate]) -> None:
        for b in blocks:
            await self.ensure_area(user_id, b.area)
            await self.ensure_category(user_id, b.category)

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
        await self._register_block_taxonomy(user_id, data.blocks)
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
            await self._register_block_taxonomy(routine.user_id, data.blocks or [])

        await self.db.flush()
        await self.db.refresh(routine, ["blocks"])
        return routine

    async def delete(self, routine: Routine) -> None:
        await self.db.delete(routine)
        await self.db.flush()

    async def list_active_all(self) -> list[Routine]:
        result = await self.db.execute(select(Routine).where(Routine.is_active.is_(True)))
        return list(result.scalars().all())

    async def list_area_names(self, user_id: str) -> list[str]:
        result = await self.db.execute(
            select(RoutineAreaOption.name)
            .where(RoutineAreaOption.user_id == user_id)
            .order_by(RoutineAreaOption.name.asc())
        )
        return list(result.scalars().all())

    async def ensure_area(self, user_id: str, name: str) -> None:
        clean = (name or "").strip()
        if not clean:
            return
        existing = await self.db.execute(
            select(RoutineAreaOption).where(RoutineAreaOption.user_id == user_id)
        )
        for row in existing.scalars().all():
            if row.name.lower() == clean.lower():
                return
        self.db.add(RoutineAreaOption(user_id=user_id, name=clean))
        await self.db.flush()

    async def list_category_names(self, user_id: str) -> list[str]:
        result = await self.db.execute(
            select(RoutineCategoryOption.name)
            .where(RoutineCategoryOption.user_id == user_id)
            .order_by(RoutineCategoryOption.name.asc())
        )
        return list(result.scalars().all())

    async def ensure_category(self, user_id: str, name: str) -> None:
        clean = (name or "").strip()
        if not clean:
            return
        existing = await self.db.execute(
            select(RoutineCategoryOption).where(RoutineCategoryOption.user_id == user_id)
        )
        for row in existing.scalars().all():
            if row.name.lower() == clean.lower():
                return
        self.db.add(RoutineCategoryOption(user_id=user_id, name=clean))
        await self.db.flush()
