from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.wishlist.schemas import WishlistCreate, WishlistListItem, WishlistResponse, WishlistUpdate
from app.modules.wishlist.service import WishlistService

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("/items", response_model=list[WishlistListItem])
async def list_wishlist_items(
    category: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WishlistService(db).list_items(user.id, category=category)


@router.post("/items", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
async def create_wishlist_item(
    data: WishlistCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WishlistService(db).create_item(user.id, data)


@router.get("/items/{item_id}", response_model=WishlistResponse)
async def get_wishlist_item(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WishlistService(db).get_item(user.id, item_id)


@router.patch("/items/{item_id}", response_model=WishlistResponse)
async def update_wishlist_item(
    item_id: str,
    data: WishlistUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WishlistService(db).update_item(user.id, item_id, data)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist_item(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await WishlistService(db).delete_item(user.id, item_id)
