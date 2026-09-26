from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import taxonomy
from app.core.pagination import Pagination, paginate
from app.modules.wishlist.models import WishlistCategory, WishlistItem
from app.modules.wishlist.schemas import WishlistCreate, WishlistUpdate


class WishlistRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_items(
        self,
        user_id: str,
        category: str | None = None,
        status: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[WishlistItem], int]:
        q = select(WishlistItem).where(WishlistItem.user_id == user_id)
        if category:
            q = q.where(WishlistItem.category == category)
        if status == "incomplete":
            q = q.where(WishlistItem.status.in_(("in_progress", "delayed")))
        elif status:
            q = q.where(WishlistItem.status == status)
        q = q.order_by(WishlistItem.updated_at.desc())
        return await paginate(self.db, q, Pagination(limit=limit, offset=offset))

    async def list_category_names(self, user_id: str) -> list[str]:
        return await taxonomy.list_names(self.db, WishlistCategory, user_id)

    async def ensure_category(self, user_id: str, name: str) -> None:
        """Register a name for reuse (idempotent, case-insensitive)."""
        await taxonomy.ensure_name(self.db, WishlistCategory, user_id, name)

    async def get_by_id(self, user_id: str, item_id: str) -> WishlistItem | None:
        result = await self.db.execute(
            select(WishlistItem).where(WishlistItem.id == item_id, WishlistItem.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: WishlistCreate) -> WishlistItem:
        item = WishlistItem(user_id=user_id, **data.model_dump())
        self.db.add(item)
        await self.db.flush()
        if data.category:
            await self.ensure_category(user_id, data.category)
        await self.db.refresh(item)
        return item

    async def update(self, item: WishlistItem, data: WishlistUpdate) -> WishlistItem:
        fields = data.model_dump(exclude_unset=True)
        for key, value in fields.items():
            setattr(item, key, value)
        if "category" in fields and fields["category"]:
            await self.ensure_category(item.user_id, fields["category"])
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item: WishlistItem) -> None:
        await self.db.delete(item)
        await self.db.flush()
