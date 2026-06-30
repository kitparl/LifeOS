from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.life_timeline.repository import LifeTimelineRepository
from app.modules.life_timeline.schemas import (
    LifeTimelineItem,
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
)
from app.modules.memory.repository import MemoryRepository
from app.modules.timeline.schemas import TimelineItem
from app.modules.timeline.service import TimelineService


class LifeTimelineService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = LifeTimelineRepository(db)
        self.timeline = TimelineService(db)
        self.memory_repo = MemoryRepository(db)

    async def list_complete(self, user_id: str, limit: int = 150) -> list[LifeTimelineItem]:
        items: list[LifeTimelineItem] = []

        events: list[TimelineItem] = await self.timeline.list_events(user_id, limit=limit)
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

        milestones = await self.repo.list_milestones(user_id)
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

        memories = await self.memory_repo.list_items(user_id)
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
        return items[:limit]

    async def list_milestones(self, user_id: str) -> list[MilestoneResponse]:
        ms = await self.repo.list_milestones(user_id)
        return [MilestoneResponse.model_validate(m) for m in ms]

    async def create_milestone(self, user_id: str, data: MilestoneCreate) -> MilestoneResponse:
        m = await self.repo.create(user_id, data)
        return MilestoneResponse.model_validate(m)

    async def update_milestone(
        self, user_id: str, milestone_id: str, data: MilestoneUpdate
    ) -> MilestoneResponse:
        m = await self.repo.get_milestone(user_id, milestone_id)
        if not m:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Milestone not found")
        updated = await self.repo.update(m, data)
        return MilestoneResponse.model_validate(updated)

    async def delete_milestone(self, user_id: str, milestone_id: str) -> None:
        m = await self.repo.get_milestone(user_id, milestone_id)
        if not m:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Milestone not found")
        await self.repo.delete(m)
