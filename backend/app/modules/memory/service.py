from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memory.repository import MemoryRepository
from app.modules.memory.schemas import MemoryCreate, MemoryResponse, MemorySummary, MemoryUpdate


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.repo = MemoryRepository(db)

    async def list_items(self, user_id: str, category: str | None = None) -> list[MemoryResponse]:
        items = await self.repo.list_items(user_id, category)
        return [MemoryResponse.model_validate(i) for i in items]

    async def get_item(self, user_id: str, item_id: str) -> MemoryResponse:
        item = await self.repo.get_by_id(user_id, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Memory item not found")
        return MemoryResponse.model_validate(item)

    async def create_item(self, user_id: str, data: MemoryCreate) -> MemoryResponse:
        item = await self.repo.create(user_id, data)
        return MemoryResponse.model_validate(item)

    async def update_item(self, user_id: str, item_id: str, data: MemoryUpdate) -> MemoryResponse:
        item = await self.repo.get_by_id(user_id, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Memory item not found")
        updated = await self.repo.update(item, data)
        return MemoryResponse.model_validate(updated)

    async def delete_item(self, user_id: str, item_id: str) -> None:
        item = await self.repo.get_by_id(user_id, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Memory item not found")
        await self.repo.delete(item)

    async def summary(self, user_id: str) -> MemorySummary:
        items = await self.repo.list_items(user_id)
        by_category = await self.repo.count_by_category(user_id)
        prefs = [MemoryResponse.model_validate(i) for i in items if i.category == "preference"][:5]
        return MemorySummary(total=len(items), by_category=by_category, top_preferences=prefs)
