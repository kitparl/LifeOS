from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memory.models import AiMemoryItem
from app.modules.memory.schemas import MemoryCreate, MemoryUpdate


class MemoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_items(self, user_id: str, category: str | None = None) -> list[AiMemoryItem]:
        q = select(AiMemoryItem).where(AiMemoryItem.user_id == user_id)
        if category:
            q = q.where(AiMemoryItem.category == category)
        q = q.order_by(AiMemoryItem.importance.desc(), AiMemoryItem.updated_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, item_id: str) -> AiMemoryItem | None:
        result = await self.db.execute(
            select(AiMemoryItem).where(AiMemoryItem.id == item_id, AiMemoryItem.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: MemoryCreate) -> AiMemoryItem:
        item = AiMemoryItem(user_id=user_id, **data.model_dump())
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update(self, item: AiMemoryItem, data: MemoryUpdate) -> AiMemoryItem:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item: AiMemoryItem) -> None:
        await self.db.delete(item)

    async def count_by_category(self, user_id: str) -> dict[str, int]:
        result = await self.db.execute(
            select(AiMemoryItem.category, func.count())
            .where(AiMemoryItem.user_id == user_id)
            .group_by(AiMemoryItem.category)
        )
        return {row[0]: int(row[1]) for row in result.all()}
