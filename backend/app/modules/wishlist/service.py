from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.wishlist.repository import WishlistRepository
from app.modules.wishlist.schemas import WishlistCreate, WishlistListItem, WishlistResponse, WishlistUpdate


class WishlistService:
    def __init__(self, db: AsyncSession):
        self.repo = WishlistRepository(db)

    async def list_items(self, user_id: str, category: str | None = None) -> list[WishlistListItem]:
        items = await self.repo.list_items(user_id, category=category)
        return [WishlistListItem.model_validate(i) for i in items]

    async def get_item(self, user_id: str, item_id: str) -> WishlistResponse:
        item = await self.repo.get_by_id(user_id, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")
        return WishlistResponse.model_validate(item)

    async def create_item(self, user_id: str, data: WishlistCreate) -> WishlistResponse:
        item = await self.repo.create(user_id, data)
        return WishlistResponse.model_validate(item)

    async def update_item(self, user_id: str, item_id: str, data: WishlistUpdate) -> WishlistResponse:
        item = await self.repo.get_by_id(user_id, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")
        updated = await self.repo.update(item, data)
        return WishlistResponse.model_validate(updated)

    async def delete_item(self, user_id: str, item_id: str) -> None:
        item = await self.repo.get_by_id(user_id, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")
        await self.repo.delete(item)
