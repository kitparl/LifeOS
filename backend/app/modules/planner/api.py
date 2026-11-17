from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.planner.schemas import (
    PlannerContentResponse,
    PlannerContentUpdate,
    PlannerNodeCreate,
    PlannerNodeResponse,
    PlannerNodeUpdate,
)
from app.modules.planner.service import PlannerService

router = APIRouter(prefix="/planner", tags=["planner"])


@router.get("/nodes", response_model=list[PlannerNodeResponse])
async def list_planner_nodes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PlannerService(db).list_nodes(user.id)


@router.post("/nodes", response_model=PlannerNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_planner_node(
    data: PlannerNodeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PlannerService(db).create_node(user.id, data)


@router.patch("/nodes/{node_id}", response_model=PlannerNodeResponse)
async def update_planner_node(
    node_id: str,
    data: PlannerNodeUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PlannerService(db).update_node(user.id, node_id, data)


@router.post(
    "/nodes/{node_id}/duplicate", response_model=PlannerNodeResponse, status_code=status.HTTP_201_CREATED
)
async def duplicate_planner_node(
    node_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PlannerService(db).duplicate_node(user.id, node_id)


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planner_node(
    node_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await PlannerService(db).delete_node(user.id, node_id)


@router.get("/nodes/{node_id}/content", response_model=PlannerContentResponse)
async def get_planner_content(
    node_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PlannerService(db).get_content(user.id, node_id)


@router.put("/nodes/{node_id}/content", response_model=PlannerContentResponse)
async def save_planner_content(
    node_id: str,
    data: PlannerContentUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PlannerService(db).save_content(user.id, node_id, data)
