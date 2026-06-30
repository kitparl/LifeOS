from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.life_timeline.models import LifeMilestone
from app.modules.life_timeline.schemas import MilestoneCreate, MilestoneUpdate


class LifeTimelineRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_milestones(self, user_id: str) -> list[LifeMilestone]:
        result = await self.db.execute(
            select(LifeMilestone)
            .where(LifeMilestone.user_id == user_id)
            .order_by(LifeMilestone.milestone_date.desc())
        )
        return list(result.scalars().all())

    async def get_milestone(self, user_id: str, milestone_id: str) -> LifeMilestone | None:
        result = await self.db.execute(
            select(LifeMilestone).where(
                LifeMilestone.id == milestone_id, LifeMilestone.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: MilestoneCreate) -> LifeMilestone:
        m = LifeMilestone(user_id=user_id, **data.model_dump())
        self.db.add(m)
        await self.db.flush()
        await self.db.refresh(m)
        return m

    async def update(self, milestone: LifeMilestone, data: MilestoneUpdate) -> LifeMilestone:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(milestone, key, value)
        await self.db.flush()
        await self.db.refresh(milestone)
        return milestone

    async def delete(self, milestone: LifeMilestone) -> None:
        await self.db.delete(milestone)
