from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.routines.schemas import (
    RoutineCreate,
    RoutineListItem,
    RoutineResponse,
    RoutineUpdate,
    TaxonomyNameCreate,
)
from app.modules.routines.service import RoutineService

router = APIRouter(prefix="/routines", tags=["routines"])


@router.get("", response_model=list[RoutineListItem])
async def list_routines(
    response: Response,
    active_only: bool = Query(default=False),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await RoutineService(db).list_routines(
        user.id, active_only=active_only, limit=limit, offset=offset
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/areas", response_model=list[str])
async def list_routine_areas(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RoutineService(db).list_areas(user.id)


@router.post("/areas", response_model=list[str], status_code=status.HTTP_201_CREATED)
async def create_routine_area(
    data: TaxonomyNameCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await RoutineService(db).create_area(user.id, data.name)
    return await RoutineService(db).list_areas(user.id)


@router.get("/categories", response_model=list[str])
async def list_routine_categories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RoutineService(db).list_categories(user.id)


@router.post("/categories", response_model=list[str], status_code=status.HTTP_201_CREATED)
async def create_routine_category(
    data: TaxonomyNameCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await RoutineService(db).create_category(user.id, data.name)
    return await RoutineService(db).list_categories(user.id)


@router.post("", response_model=RoutineResponse, status_code=status.HTTP_201_CREATED)
async def create_routine(
    data: RoutineCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RoutineService(db).create_routine(user.id, data)


@router.get("/by-block/{block_id}", response_model=RoutineResponse)
async def get_routine_by_block(
    block_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RoutineService(db).get_by_block(user.id, block_id)


@router.get("/{routine_id}", response_model=RoutineResponse)
async def get_routine(
    routine_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RoutineService(db).get_routine(user.id, routine_id)


@router.patch("/{routine_id}", response_model=RoutineResponse)
async def update_routine(
    routine_id: str,
    data: RoutineUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RoutineService(db).update_routine(user.id, routine_id, data)


@router.delete("/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routine(
    routine_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await RoutineService(db).delete_routine(user.id, routine_id)
