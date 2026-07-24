from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.integrations.digest_service import DigestService
from app.modules.integrations.schemas import (
    DetectChatIdRequest,
    DetectChatIdResponse,
    DigestResponse,
    IntegrationCreate,
    IntegrationProviderInfo,
    IntegrationResponse,
    IntegrationSyncResponse,
    IntegrationUpdate,
    TelegramConfigStatus,
    TelegramConfigUpdate,
    TelegramTestResponse,
)
from app.modules.integrations.service import IntegrationService, list_integration_providers

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/providers", response_model=list[IntegrationProviderInfo])
async def list_providers():
    return list_integration_providers()


@router.get("/telegram", response_model=TelegramConfigStatus)
async def get_telegram_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationService(db).get_telegram_status(user.id)


@router.put("/telegram/config", response_model=TelegramConfigStatus)
async def save_telegram_config(
    data: TelegramConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationService(db).save_telegram_config(user.id, data)


@router.post("/telegram/digest", response_model=DigestResponse)
async def send_telegram_digest(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DigestService(db).send_digest(user.id)


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


@router.post("/{conn_id}/test", response_model=TelegramTestResponse)
async def test_integration(
    conn_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationService(db).test_connection(user.id, conn_id)


@router.post("/{conn_id}/detect-chat-id", response_model=DetectChatIdResponse)
async def detect_chat_id(
    conn_id: str,
    data: DetectChatIdRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    override = data.bot_token if data else None
    return await IntegrationService(db).detect_chat_id(user.id, conn_id, bot_token_override=override)
