from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.career.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    CareerProfileResponse,
    CareerProfileUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.modules.career.service import CareerService

router = APIRouter(prefix="/career", tags=["career"])


@router.get("/profile", response_model=CareerProfileResponse)
async def get_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await CareerService(db).get_profile(user.id)


@router.patch("/profile", response_model=CareerProfileResponse)
async def update_profile(
    data: CareerProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CareerService(db).update_profile(user.id, data)


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await CareerService(db).list_projects(user.id)


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CareerService(db).create_project(user.id, data)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CareerService(db).get_project(user.id, project_id)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CareerService(db).update_project(user.id, project_id, data)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await CareerService(db).delete_project(user.id, project_id)


@router.get("/applications", response_model=list[ApplicationResponse])
async def list_applications(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await CareerService(db).list_applications(user.id)


@router.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CareerService(db).create_application(user.id, data)


@router.patch("/applications/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: str,
    data: ApplicationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CareerService(db).update_application(user.id, app_id, data)


@router.delete("/applications/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    app_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await CareerService(db).delete_application(user.id, app_id)


@router.get("/analytics")
async def career_analytics(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await CareerService(db).analytics(user.id)
