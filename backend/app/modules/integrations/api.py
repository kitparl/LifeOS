from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.integrations.digest_service import DigestService
from app.modules.integrations.schemas import (
    DetectChatIdRequest,
    DetectChatIdResponse,
    DigestResponse,
    GitHubConfigStatus,
    GitHubConfigUpdate,
    GitHubSyncResponse,
    GitHubTestResponse,
    IntegrationCreate,
    IntegrationProviderInfo,
    IntegrationResponse,
    IntegrationSyncResponse,
    IntegrationUpdate,
    ReportRunResponse,
    TelegramConfigStatus,
    TelegramConfigUpdate,
    TelegramTestResponse,
    TelegramWebhookRegisterResponse,
    TelegramWebhookStatus,
)
from app.modules.integrations.github_sync_service import GitHubSyncService
from app.modules.integrations.service import IntegrationService, list_integration_providers
from app.modules.integrations.webhook_service import TelegramWebhookService

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/providers", response_model=list[IntegrationProviderInfo])
async def list_providers():
    return list_integration_providers()


@router.get("/telegram", response_model=TelegramConfigStatus)
async def get_telegram_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    status_resp = await IntegrationService(db).get_telegram_status(user.id)
    try:
        wh = await TelegramWebhookService(db).webhook_status(user.id)
        if wh.url:
            status_resp.webhook_url = wh.url
            status_resp.webhook_configured = True
    except Exception:
        pass
    return status_resp


@router.put("/telegram/config", response_model=TelegramConfigStatus)
async def save_telegram_config(
    data: TelegramConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationService(db).save_telegram_config(user.id, data)


@router.get("/github", response_model=GitHubConfigStatus)
async def get_github_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationService(db).get_github_status(user.id)


@router.put("/github/config", response_model=GitHubConfigStatus)
async def save_github_config(
    data: GitHubConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationService(db).save_github_config(user.id, data)


@router.post("/github/test", response_model=GitHubTestResponse)
async def test_github(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await IntegrationService(db).test_github(user.id)


@router.post("/github/sync/section/{section_id}", response_model=GitHubSyncResponse)
async def sync_github_section(
    section_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await GitHubSyncService(db).sync_section(user.id, section_id)
    return GitHubSyncResponse(**result)


@router.post("/telegram/digest", response_model=DigestResponse)
async def send_telegram_digest(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DigestService(db).send_digest(user.id)


@router.post("/telegram/reports/{job_type}/run", response_model=DigestResponse)
async def run_scheduled_report(
    job_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually fire a scheduled report (morning/midday/night/weekly/ai_briefing)."""
    from fastapi import HTTPException

    from app.modules.integrations.scheduled_report_service import CRON_JOB_TYPES, ScheduledReportService

    if job_type not in CRON_JOB_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"job_type must be one of: {', '.join(CRON_JOB_TYPES)}",
        )
    return await ScheduledReportService(db).run(user.id, job_type)


@router.get("/telegram/report-runs", response_model=list[ReportRunResponse])
async def list_report_runs(
    job_type: str | None = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.modules.integrations.report_repository import ReportRunRepository

    runs = await ReportRunRepository(db).list_runs(user.id, job_type=job_type, limit=min(limit, 200))
    return [ReportRunResponse.model_validate(r) for r in runs]


@router.post("/telegram/webhook/register", response_model=TelegramWebhookRegisterResponse)
async def register_telegram_webhook(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TelegramWebhookService(db).register_webhook(user.id)


@router.delete("/telegram/webhook", response_model=TelegramWebhookRegisterResponse)
async def delete_telegram_webhook(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TelegramWebhookService(db).delete_webhook(user.id)


@router.get("/telegram/webhook", response_model=TelegramWebhookStatus)
async def get_telegram_webhook_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TelegramWebhookService(db).webhook_status(user.id)


@router.post("/telegram/webhook/{secret}")
async def telegram_webhook(
    secret: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    """Inbound Telegram updates. Authenticated by path secret (+ optional header)."""
    payload = await request.json()
    return await TelegramWebhookService(db).handle_update(
        secret,
        payload if isinstance(payload, dict) else {},
        header_secret=x_telegram_bot_api_secret_token,
    )


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
