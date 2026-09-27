from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.pagination import Pagination, pagination_params
from app.modules.auth.models import User
from app.modules.travel.schemas.places import (
    NearPlaceOut,
    PlaceCreate,
    PlaceHistory,
    PlaceOut,
    PlaceStatus,
    PlaceUpdate,
    TagsUpdate,
)
from app.modules.travel.services.place_service import PlaceService

router = APIRouter()


@router.get("/places", response_model=list[PlaceOut])
async def list_places(
    response: Response,
    status_filter: PlaceStatus | None = Query(default=None, alias="status"),
    category: str | None = Query(default=None, max_length=32),
    tag: str | None = Query(default=None, max_length=32),
    q: str | None = Query(default=None, max_length=100),
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await PlaceService(db).list_places(
        user.id, status=status_filter, category=category, tag=tag, q=q, pagination=pagination
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/places", response_model=PlaceOut, status_code=status.HTTP_201_CREATED)
async def create_place(data: PlaceCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await PlaceService(db).create(user.id, data)


@router.get("/places/near", response_model=list[NearPlaceOut])
async def places_near(
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    radius_km: float = Query(default=100, gt=0, le=5000),
    status_filter: PlaceStatus | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PlaceService(db).near(user.id, lat, lng, radius_km, status_filter)


@router.get("/places/{place_id}", response_model=PlaceOut)
async def get_place(place_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await PlaceService(db).get(user.id, place_id)


@router.patch("/places/{place_id}", response_model=PlaceOut)
async def update_place(
    place_id: str, data: PlaceUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await PlaceService(db).update(user.id, place_id, data)


@router.delete("/places/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(place_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await PlaceService(db).delete(user.id, place_id)


@router.get("/places/{place_id}/history", response_model=PlaceHistory)
async def place_history(place_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await PlaceService(db).history(user.id, place_id)


@router.put("/places/{place_id}/tags", response_model=PlaceOut)
async def set_place_tags(
    place_id: str, data: TagsUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await PlaceService(db).set_tags(user.id, place_id, data.names)


@router.get("/tags", response_model=list[str])
async def list_tags(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await PlaceService(db).list_tags(user.id)
