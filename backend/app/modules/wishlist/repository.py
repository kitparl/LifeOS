from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.wishlist.models import WishlistItem
from app.modules.wishlist.schemas import WishlistCreate, WishlistUpdate


class WishlistRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_items(self, user_id: str, category: str | None = None) -> list[WishlistItem]:
        q = select(WishlistItem).where(WishlistItem.user_id == user_id)
        if category:
            q = q.where(WishlistItem.category == category)
        q = q.order_by(WishlistItem.updated_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, item_id: str) -> WishlistItem | None:
        result = await self.db.execute(
            select(WishlistItem).where(WishlistItem.id == item_id, WishlistItem.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: WishlistCreate) -> WishlistItem:
        item = WishlistItem(user_id=user_id, **data.model_dump())
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update(self, item: WishlistItem, data: WishlistUpdate) -> WishlistItem:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item: WishlistItem) -> None:
        await self.db.delete(item)
        await self.db.flush()
