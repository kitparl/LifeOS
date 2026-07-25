from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.wishlist.models import SUGGESTED_WISHLIST_CATEGORIES
from app.modules.wishlist.repository import WishlistRepository
from app.modules.wishlist.schemas import WishlistCreate, WishlistListItem, WishlistResponse, WishlistUpdate


class WishlistService:
    def __init__(self, db: AsyncSession):
        self.repo = WishlistRepository(db)

    async def list_items(
        self,
        user_id: str,
        category: str | None = None,
        status: str | None = None,
    ) -> list[WishlistListItem]:
        items = await self.repo.list_items(user_id, category=category, status=status)
        return [WishlistListItem.model_validate(i) for i in items]

    async def list_categories(self, user_id: str) -> list[str]:
        """Suggested defaults + user-created, de-duplicated (CI) and sorted."""
        stored = await self.repo.list_category_names(user_id)
        seen: dict[str, str] = {}
        for name in [*SUGGESTED_WISHLIST_CATEGORIES, *stored]:
            key = name.strip().lower()
            if key and key not in seen:
                seen[key] = name.strip()
        return sorted(seen.values(), key=str.lower)

    async def create_category(self, user_id: str, name: str) -> str:
        clean = name.strip()
        if not clean:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name required")
        await self.repo.ensure_category(user_id, clean)
        return clean

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
