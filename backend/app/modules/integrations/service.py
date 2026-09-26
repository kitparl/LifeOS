import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, get_or_404
from app.core.timezone import utc_now
from app.modules.ai.adapters.registry import AI_PROVIDERS
from app.modules.integrations.google_calendar.config import parse_config as parse_google_calendar_config
from app.modules.integrations.models import INTEGRATION_PROVIDERS
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    IntegrationCreate,
    IntegrationProviderInfo,
    IntegrationResponse,
    IntegrationSyncResponse,
    IntegrationUpdate,
)

logger = logging.getLogger(__name__)

PROVIDER_CATALOG: list[IntegrationProviderInfo] = [
    IntegrationProviderInfo(provider="github", display_name="GitHub", description="Sync Knowledge Notes to a repository", oauth_required=False),
    IntegrationProviderInfo(provider="google_calendar", display_name="Google Calendar", description="Import Google Calendar events (optional two-way)", oauth_required=True),
    IntegrationProviderInfo(provider="google_fit", display_name="Google Fit", description="Activity and health metrics", oauth_required=True),
    IntegrationProviderInfo(provider="apple_health", display_name="Apple Health", description="Health data import", oauth_required=True),
    IntegrationProviderInfo(provider="garmin", display_name="Garmin", description="Runs and workouts", oauth_required=True),
    IntegrationProviderInfo(provider="strava", display_name="Strava", description="Running activities", oauth_required=True),
    IntegrationProviderInfo(provider="telegram", display_name="Telegram", description="Notifications and bot commands", oauth_required=False),
    IntegrationProviderInfo(provider="email", display_name="Email", description="Digest and reminders", oauth_required=False),
    IntegrationProviderInfo(provider="openai", display_name="OpenAI", description="GPT models for chat, writing, and embeddings", oauth_required=False, group="ai"),
    IntegrationProviderInfo(provider="anthropic", display_name="Anthropic", description="Claude models for chat and writing", oauth_required=False, group="ai"),
    IntegrationProviderInfo(provider="gemini", display_name="Google Gemini", description="Gemini models for chat and writing", oauth_required=False, group="ai"),
    IntegrationProviderInfo(provider="sarvam", display_name="Sarvam AI", description="Sarvam models for chat and writing", oauth_required=False, group="ai"),
    IntegrationProviderInfo(provider="mistral", display_name="Mistral AI", description="Mistral models for chat and writing", oauth_required=False, group="ai"),
    IntegrationProviderInfo(provider="groq", display_name="Groq", description="Fast open models (Llama, Qwen, and more)", oauth_required=False, group="ai"),
    IntegrationProviderInfo(provider="xai", display_name="xAI", description="Grok models for chat and writing", oauth_required=False, group="ai"),
    IntegrationProviderInfo(provider="deepseek", display_name="DeepSeek", description="DeepSeek chat and reasoning models", oauth_required=False, group="ai"),
    IntegrationProviderInfo(provider="together", display_name="Together AI", description="Open-source models (Llama, Qwen, and more)", oauth_required=False, group="ai"),
    IntegrationProviderInfo(provider="openrouter", display_name="OpenRouter", description="Many vendors' models through one key", oauth_required=False, group="ai"),
    IntegrationProviderInfo(provider="perplexity", display_name="Perplexity", description="Sonar models with web search", oauth_required=False, group="ai"),
    IntegrationProviderInfo(provider="wordnik", display_name="Wordnik", description="Dictionary, related words, and Word of the Day", oauth_required=False, group="language"),
]

# Providers whose config_json holds encrypted secrets and is managed only by dedicated endpoints.
_SECRET_CONFIG_PROVIDERS = frozenset({"telegram", "github", "google_calendar", "wordnik", *AI_PROVIDERS})

def list_integration_providers() -> list[IntegrationProviderInfo]:
    return PROVIDER_CATALOG

def _safe_response(conn) -> IntegrationResponse:
    """Never expose raw bot tokens in API responses."""
    resp = IntegrationResponse.model_validate(conn)
    if conn.provider in _SECRET_CONFIG_PROVIDERS:
        # Encrypted config is not useful to the client; omit secrets entirely.
        resp.config_json = None
    return resp

class IntegrationService:
    def __init__(self, db: AsyncSession):
        self.repo = IntegrationRepository(db)

    async def list_connections(
        self, user_id: str, limit: int = 25, offset: int = 0
    ) -> tuple[list[IntegrationResponse], int]:
        conns, total = await self.repo.list_connections(user_id, limit=limit, offset=offset)
        return [_safe_response(c) for c in conns], total

    async def create_connection(self, user_id: str, data: IntegrationCreate) -> IntegrationResponse:
        if data.provider not in INTEGRATION_PROVIDERS:
            raise BadRequestError(f"Unknown provider: {data.provider}")
        existing = await self.repo.get_by_provider(user_id, data.provider)
        if existing:
            raise ConflictError("Integration already exists for this provider")
        catalog = next((p for p in PROVIDER_CATALOG if p.provider == data.provider), None)
        display_name = data.display_name or (catalog.display_name if catalog else data.provider)
        # Telegram secrets must go through save_telegram_config (encrypted).
        create_data = data
        if data.provider in _SECRET_CONFIG_PROVIDERS and data.config_json:
            create_data = data.model_copy(update={"config_json": None})
        if data.provider == "google_calendar":
            # Tokens only arrive via the OAuth callback; never accept raw config,
            # and never enable before OAuth has produced a refresh token.
            create_data = data.model_copy(update={"config_json": None, "enabled": False})
        conn = await self.repo.create(user_id, create_data, display_name)
        return _safe_response(conn)

    async def update_connection(
        self, user_id: str, conn_id: str, data: IntegrationUpdate
    ) -> IntegrationResponse:
        conn = get_or_404(await self.repo.get_by_id(user_id, conn_id), "Integration not found")
        update_data = data
        if conn.provider in _SECRET_CONFIG_PROVIDERS:
            # Ignore raw config_json on generic PATCH; secrets go through the dedicated
            # config endpoints. Drop the field entirely: model_copy(update={"config_json": None})
            # would mark it as set, and repo.update would then wipe the stored config.
            update_data = IntegrationUpdate(**data.model_dump(exclude_unset=True, exclude={"config_json"}))
        if (
            conn.provider == "google_calendar"
            and data.enabled
            and not parse_google_calendar_config(conn.config_json).connected
        ):
            raise BadRequestError("Connect Google Calendar from Integrations before enabling it")
        updated = await self.repo.update(conn, update_data)
        return _safe_response(updated)

    async def delete_connection(self, user_id: str, conn_id: str) -> None:
        conn = get_or_404(await self.repo.get_by_id(user_id, conn_id), "Integration not found")
        if conn.provider == "telegram":
            try:
                from app.modules.integrations.scheduling.scheduler import remove_user_digest_job

                remove_user_digest_job(user_id)
            except Exception:
                logger.exception("Failed to remove scheduled jobs for user=%s", user_id)
        if conn.provider == "google_calendar":
            from app.modules.integrations.google_calendar.sync_service import GoogleCalendarSyncService

            await GoogleCalendarSyncService(self.repo.db).disconnect(user_id)
            return
        await self.repo.delete(conn)

    async def sync_connection(self, user_id: str, conn_id: str) -> IntegrationSyncResponse:
        conn = get_or_404(await self.repo.get_by_id(user_id, conn_id), "Integration not found")
        if not conn.enabled:
            raise BadRequestError("Integration is disabled")
        if conn.provider == "github":
            raise BadRequestError("Use POST /integrations/github/sync/section/{section_id} to sync notes")
        if conn.provider == "google_calendar":
            from app.modules.integrations.google_calendar.sync_service import GoogleCalendarSyncService

            return await GoogleCalendarSyncService(self.repo.db).sync(user_id)
        now = utc_now()
        conn.last_sync_at = now
        conn.status = "synced"
        await self.repo.update(conn, IntegrationUpdate())
        return IntegrationSyncResponse(
            provider=conn.provider,
            status="stub_sync",
            message=f"Stub sync completed for {conn.provider}. Configure OAuth credentials for live sync.",
            synced_at=now,
        )
