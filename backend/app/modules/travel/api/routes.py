from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.travel.schemas.routes import RouteDetail, RouteDraw, RouteUpdate
from app.modules.travel.services.route_service import RouteService

router = APIRouter(prefix="/routes")


@router.post("", response_model=RouteDetail, status_code=status.HTTP_201_CREATED)
async def save_drawn_route(data: RouteDraw, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await RouteService(db).save_drawn(user.id, data)


@router.get("/{route_id}", response_model=RouteDetail)
async def get_route(route_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await RouteService(db).get(user.id, route_id)


@router.patch("/{route_id}", response_model=RouteDetail)
async def rename_route(
    route_id: str, data: RouteUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await RouteService(db).rename(user.id, route_id, data.name)


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(route_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await RouteService(db).delete(user.id, route_id)
