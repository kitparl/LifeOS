from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.routines.models import Routine, RoutineBlock
from app.modules.routines.schemas import RoutineBlockCreate, RoutineCreate, RoutineUpdate


class RoutineRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_routines(self, user_id: str, active_only: bool = False) -> list[Routine]:
        q = (
            select(Routine)
            .where(Routine.user_id == user_id)
            .options(selectinload(Routine.blocks))
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
            .options(selectinload(Routine.blocks))
        )
        return result.scalar_one_or_none()

    async def get_by_block_id(self, user_id: str, block_id: str) -> Routine | None:
        result = await self.db.execute(
            select(Routine)
            .join(RoutineBlock)
            .where(RoutineBlock.id == block_id, Routine.user_id == user_id)
            .options(selectinload(Routine.blocks))
        )
        return result.scalar_one_or_none()

    def _make_blocks(self, blocks: list[RoutineBlockCreate]) -> list[RoutineBlock]:
        return [
            RoutineBlock(
                title=b.title,
                start_time=b.start_time,
                end_time=b.end_time,
                area=b.area,
                category=b.category,
                notes=b.notes,
                sort_order=b.sort_order if b.sort_order else i,
            )
            for i, b in enumerate(blocks)
        ]

    async def create(self, user_id: str, data: RoutineCreate) -> Routine:
        routine = Routine(
            user_id=user_id,
            name=data.name,
            description=data.description,
            timezone=data.timezone,
        )
        routine.days_of_week = data.days_of_week
        routine.blocks = self._make_blocks(data.blocks)
        self.db.add(routine)
        await self.db.flush()
        await self.db.refresh(routine, ["blocks"])
        return routine

    async def update(self, routine: Routine, data: RoutineUpdate) -> Routine:
        payload = data.model_dump(exclude_unset=True)
        blocks = payload.pop("blocks", None)
        days = payload.pop("days_of_week", None)

        for key, value in payload.items():
            setattr(routine, key, value)
        if days is not None:
            routine.days_of_week = days
        if blocks is not None:
            routine.blocks.clear()
            await self.db.flush()
            routine.blocks = self._make_blocks(data.blocks or [])

        await self.db.flush()
        await self.db.refresh(routine, ["blocks"])
        return routine

    async def delete(self, routine: Routine) -> None:
        await self.db.delete(routine)
        await self.db.flush()
