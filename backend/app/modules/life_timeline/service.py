from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.life_timeline.repository import LifeTimelineRepository
from app.modules.life_timeline.schemas import (
    LifeTimelineItem,
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
)
from app.modules.memory.repository import MemoryRepository
from app.modules.timeline.service import TimelineService
from app.core.exceptions import get_or_404

class LifeTimelineService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = LifeTimelineRepository(db)
        self.timeline = TimelineService(db)
        self.memory_repo = MemoryRepository(db)

    async def list_complete(
        self, user_id: str, limit: int = 25, offset: int = 0
    ) -> tuple[list[LifeTimelineItem], int]:
        items: list[LifeTimelineItem] = []

        events, _ = await self.timeline.list_events(user_id, limit=None)
        for e in events:
            items.append(
                LifeTimelineItem(
                    item_type="event",
                    module=e.module,
                    id=e.id,
                    title=e.title,
                    occurred_at=e.occurred_at,
                    route=e.route,
                )
            )

        milestones, _ = await self.repo.list_milestones(user_id, limit=None)
        for m in milestones:
            at = datetime.combine(m.milestone_date, datetime.min.time()).replace(
                tzinfo=m.created_at.tzinfo
            )
            items.append(
                LifeTimelineItem(
                    item_type="milestone",
                    module="life_timeline",
                    id=m.id,
                    title=m.title,
                    description=m.description,
                    occurred_at=at,
                    route="/life-timeline",
                    photo_file_ids=m.photo_file_ids,
                    ai_generated=m.ai_generated,
                    tags=m.tags,
                )
            )

        memories, _ = await self.memory_repo.list_items(user_id, limit=None)
        for mem in memories[:20]:
            items.append(
                LifeTimelineItem(
                    item_type="memory",
                    module="memory",
                    id=mem.id,
                    title=mem.memory_key,
                    description=mem.memory_value,
                    occurred_at=mem.created_at,
                    route="/memory",
                    ai_generated=True,
                    tags=mem.category,
                )
            )

        items.sort(key=lambda x: x.occurred_at, reverse=True)
        total = len(items)
        return items[offset : offset + limit], total

    async def list_milestones(
        self, user_id: str, limit: int = 25, offset: int = 0
    ) -> tuple[list[MilestoneResponse], int]:
        ms, total = await self.repo.list_milestones(user_id, limit=limit, offset=offset)
        return [MilestoneResponse.model_validate(m) for m in ms], total

    async def create_milestone(self, user_id: str, data: MilestoneCreate) -> MilestoneResponse:
        m = await self.repo.create(user_id, data)
        return MilestoneResponse.model_validate(m)

    async def update_milestone(
        self, user_id: str, milestone_id: str, data: MilestoneUpdate
    ) -> MilestoneResponse:
        m = get_or_404(await self.repo.get_milestone(user_id, milestone_id), "Milestone not found")
        updated = await self.repo.update(m, data)
        return MilestoneResponse.model_validate(updated)

    async def delete_milestone(self, user_id: str, milestone_id: str) -> None:
        m = get_or_404(await self.repo.get_milestone(user_id, milestone_id), "Milestone not found")
        await self.repo.delete(m)
