from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.repository import LearningRepository
from app.modules.learning.schemas import LearningCreate, LearningListItem, LearningResponse, LearningUpdate


class LearningService:
    def __init__(self, db: AsyncSession):
        self.repo = LearningRepository(db)

    async def list_items(self, user_id: str, item_type: str | None = None) -> list[LearningListItem]:
        items = await self.repo.list_items(user_id, item_type)
        return [LearningListItem.model_validate(i) for i in items]

    async def get_item(self, user_id: str, item_id: str) -> LearningResponse:
        item = await self.repo.get_by_id(user_id, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning item not found")
        return LearningResponse.model_validate(item)

    async def create_item(self, user_id: str, data: LearningCreate) -> LearningResponse:
        item = await self.repo.create(user_id, data)
        return LearningResponse.model_validate(item)

    async def update_item(self, user_id: str, item_id: str, data: LearningUpdate) -> LearningResponse:
        item = await self.repo.get_by_id(user_id, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning item not found")
        updated = await self.repo.update(item, data)
        return LearningResponse.model_validate(updated)

    async def delete_item(self, user_id: str, item_id: str) -> None:
        item = await self.repo.get_by_id(user_id, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning item not found")
        await self.repo.delete(item)
