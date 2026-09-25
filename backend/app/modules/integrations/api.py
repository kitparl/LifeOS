from typing import Literal

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.integrations.scheduling.digest_service import DigestService
from app.modules.integrations.ai.service import AiProviderIntegrationService
from app.modules.integrations.schemas import (
    AiModelAdd,
    AiModelRef,
    AiModelsResponse,
    AiModelTestResponse,
    AiProviderConfigStatus,
    AiProviderConfigUpdate,
    AiProviderTestResponse,
    DetectChatIdRequest,
    DetectChatIdResponse,
    DigestResponse,
    GitHubConfigStatus,
    GoogleCalendarConfigStatus,
    GoogleCalendarConfigUpdate,
    GoogleCalendarOAuthCallback,
    GoogleCalendarOAuthStartResponse,
    GitHubConfigUpdate,
    GitHubSyncResponse,
    GitHubTestResponse,
    IntegrationCreate,
    IntegrationProviderInfo,
    IntegrationResponse,
    IntegrationSyncResponse,
    IntegrationUpdate,
    ReportRunResponse,
    SectionSyncStatus,
    SubjectSectionSyncStatusResponse,
    TelegramConfigStatus,
    TelegramConfigUpdate,
    TelegramTestResponse,
    TelegramWebhookRegisterResponse,
    TelegramWebhookStatus,
    WordnikConfigStatus,
    WordnikConfigUpdate,
    WordnikTestResponse,
)
from app.modules.integrations.github.sync_service import GitHubSyncService
from app.modules.integrations.google_calendar.sync_service import GoogleCalendarSyncService
from app.modules.integrations.service import IntegrationService, list_integration_providers
from app.modules.integrations.telegram.webhook_service import TelegramWebhookService
from app.modules.integrations.wordnik.service import WordnikIntegrationService

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


@router.get("/google-calendar", response_model=GoogleCalendarConfigStatus)
async def get_google_calendar_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GoogleCalendarSyncService(db).get_status(user.id)


@router.put("/google-calendar/config", response_model=GoogleCalendarConfigStatus)
async def save_google_calendar_config(
    data: GoogleCalendarConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GoogleCalendarSyncService(db).save_config(user.id, data)


@router.get("/google-calendar/oauth/start", response_model=GoogleCalendarOAuthStartResponse)
async def start_google_calendar_oauth(
    mode: Literal["google_to_lifeos", "two_way"] = Query(default="google_to_lifeos"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return GoogleCalendarOAuthStartResponse(auth_url=GoogleCalendarSyncService(db).oauth_start(user.id, mode))


@router.post("/google-calendar/oauth/callback", response_model=GoogleCalendarConfigStatus)
async def complete_google_calendar_oauth(
    data: GoogleCalendarOAuthCallback,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GoogleCalendarSyncService(db).oauth_callback(user.id, data.code, data.state)


@router.post("/google-calendar/sync", response_model=IntegrationSyncResponse)
async def sync_google_calendar(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GoogleCalendarSyncService(db).sync(user.id)


@router.delete("/google-calendar", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_google_calendar(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await GoogleCalendarSyncService(db).disconnect(user.id)


@router.get("/ai/{provider}/config", response_model=AiProviderConfigStatus)
async def get_ai_provider_config(
    provider: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiProviderIntegrationService(db).status(user.id, provider)


@router.put("/ai/{provider}/config", response_model=AiProviderConfigStatus)
async def save_ai_provider_config(
    provider: str,
    data: AiProviderConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiProviderIntegrationService(db).save(user.id, provider, data)


@router.post("/ai/{provider}/test", response_model=AiProviderTestResponse)
async def test_ai_provider(
    provider: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiProviderIntegrationService(db).test(user.id, provider)


@router.get("/ai/{provider}/models", response_model=AiModelsResponse)
async def list_ai_provider_models(
    provider: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiProviderIntegrationService(db).list_models(user.id, provider)


@router.post("/ai/{provider}/models/refresh", response_model=AiModelsResponse)
async def refresh_ai_provider_models(
    provider: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiProviderIntegrationService(db).refresh_models(user.id, provider)


@router.post("/ai/{provider}/models", response_model=AiModelsResponse)
async def add_ai_provider_model(
    provider: str,
    data: AiModelAdd,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiProviderIntegrationService(db).add_model(user.id, provider, data)


@router.post("/ai/{provider}/models/remove", response_model=AiModelsResponse)
async def remove_ai_provider_model(
    provider: str,
    data: AiModelRef,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiProviderIntegrationService(db).remove_model(user.id, provider, data.model_id)


@router.post("/ai/{provider}/models/test", response_model=AiModelTestResponse)
async def test_ai_provider_model(
    provider: str,
    data: AiModelRef,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiProviderIntegrationService(db).test_model(user.id, provider, data.model_id)


@router.get("/wordnik", response_model=WordnikConfigStatus)
async def get_wordnik_config(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WordnikIntegrationService(db).status(user.id)


@router.put("/wordnik/config", response_model=WordnikConfigStatus)
async def save_wordnik_config(
    data: WordnikConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WordnikIntegrationService(db).save(user.id, data)


@router.post("/wordnik/test", response_model=WordnikTestResponse)
async def test_wordnik(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WordnikIntegrationService(db).test(user.id)


@router.post("/github/sync/section/{section_id}", response_model=GitHubSyncResponse)
async def sync_github_section(
    section_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await GitHubSyncService(db).sync_section(user.id, section_id)
    return GitHubSyncResponse(**result)


@router.get(
    "/github/sync/status/subject/{subject_id}",
    response_model=SubjectSectionSyncStatusResponse,
)
async def get_github_subject_sync_status(
    subject_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sections = await GitHubSyncService(db).get_subject_sync_statuses(user.id, subject_id)
    return SubjectSectionSyncStatusResponse(
        sections=[SectionSyncStatus(**item) for item in sections]
    )


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

    from app.modules.integrations.scheduling.scheduled_report_service import CRON_JOB_TYPES, ScheduledReportService

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
    from app.modules.integrations.reports.repository import ReportRunRepository

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
    response: Response,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await IntegrationService(db).list_connections(
        user.id, limit=limit, offset=offset
    )
    response.headers["X-Total-Count"] = str(total)
    return items


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
