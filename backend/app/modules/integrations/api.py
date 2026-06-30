from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.integrations.schemas import (
    IntegrationCreate,
    IntegrationProviderInfo,
    IntegrationResponse,
    IntegrationSyncResponse,
    IntegrationUpdate,
)
from app.modules.integrations.service import IntegrationService, list_integration_providers

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/providers", response_model=list[IntegrationProviderInfo])
async def list_providers():
    return list_integration_providers()


@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationService(db).list_connections(user.id)


@router.post("", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    data: IntegrationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationService(db).create_connection(user.id, data)


@router.patch("/{conn_id}", response_model=IntegrationResponse)
async def update_integration(
    conn_id: str,
    data: IntegrationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationService(db).update_connection(user.id, conn_id, data)


@router.delete("/{conn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    conn_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await IntegrationService(db).delete_connection(user.id, conn_id)


@router.post("/{conn_id}/sync", response_model=IntegrationSyncResponse)
async def sync_integration(
    conn_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationService(db).sync_connection(user.id, conn_id)
