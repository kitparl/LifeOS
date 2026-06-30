from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.models import LearningItem
from app.modules.learning.schemas import LearningCreate, LearningUpdate


class LearningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_items(self, user_id: str, item_type: str | None = None) -> list[LearningItem]:
        q = select(LearningItem).where(LearningItem.user_id == user_id)
        if item_type:
            q = q.where(LearningItem.item_type == item_type)
        q = q.order_by(LearningItem.updated_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, item_id: str) -> LearningItem | None:
        result = await self.db.execute(
            select(LearningItem).where(LearningItem.id == item_id, LearningItem.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: LearningCreate) -> LearningItem:
        item = LearningItem(user_id=user_id, **data.model_dump())
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update(self, item: LearningItem, data: LearningUpdate) -> LearningItem:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item: LearningItem) -> None:
        await self.db.delete(item)
