from datetime import datetime, timezone
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.models import INTEGRATION_PROVIDERS
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    ChatCandidate,
    DetectChatIdResponse,
    IntegrationCreate,
    IntegrationProviderInfo,
    IntegrationResponse,
    IntegrationSyncResponse,
    IntegrationUpdate,
    TelegramConfigStatus,
    TelegramConfigUpdate,
    TelegramTestResponse,
)
from app.modules.integrations.telegram_client import TelegramClient, TelegramClientError
from app.modules.integrations.telegram_config import (
    mask_config,
    parse_config,
    parse_preferences,
    serialize_config,
)

logger = logging.getLogger(__name__)

PROVIDER_CATALOG: list[IntegrationProviderInfo] = [
    IntegrationProviderInfo(provider="github", display_name="GitHub", description="Sync repos and commits", oauth_required=True),
    IntegrationProviderInfo(provider="google_calendar", display_name="Google Calendar", description="Two-way calendar sync", oauth_required=True),
    IntegrationProviderInfo(provider="google_fit", display_name="Google Fit", description="Activity and health metrics", oauth_required=True),
    IntegrationProviderInfo(provider="apple_health", display_name="Apple Health", description="Health data import", oauth_required=True),
    IntegrationProviderInfo(provider="garmin", display_name="Garmin", description="Runs and workouts", oauth_required=True),
    IntegrationProviderInfo(provider="strava", display_name="Strava", description="Running activities", oauth_required=True),
    IntegrationProviderInfo(provider="telegram", display_name="Telegram", description="Notifications and bot commands", oauth_required=False),
    IntegrationProviderInfo(provider="email", display_name="Email", description="Digest and reminders", oauth_required=False),
    IntegrationProviderInfo(provider="openai", display_name="OpenAI", description="AI chat and embeddings", oauth_required=False),
    IntegrationProviderInfo(provider="gemini", display_name="Gemini", description="Alternative AI provider", oauth_required=False),
]


def list_integration_providers() -> list[IntegrationProviderInfo]:
    return PROVIDER_CATALOG


def _safe_response(conn) -> IntegrationResponse:
    """Never expose raw bot tokens in API responses."""
    resp = IntegrationResponse.model_validate(conn)
    if conn.provider == "telegram":
        # Encrypted config is not useful to the client; omit secrets entirely.
        resp.config_json = None
    return resp


class IntegrationService:
    def __init__(self, db: AsyncSession):
        self.repo = IntegrationRepository(db)

    async def list_connections(self, user_id: str) -> list[IntegrationResponse]:
        conns = await self.repo.list_connections(user_id)
        return [_safe_response(c) for c in conns]

    async def create_connection(self, user_id: str, data: IntegrationCreate) -> IntegrationResponse:
        if data.provider not in INTEGRATION_PROVIDERS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown provider: {data.provider}")
        existing = await self.repo.get_by_provider(user_id, data.provider)
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, "Integration already exists for this provider")
        catalog = next((p for p in PROVIDER_CATALOG if p.provider == data.provider), None)
        display_name = data.display_name or (catalog.display_name if catalog else data.provider)
        # Telegram secrets must go through save_telegram_config (encrypted).
        create_data = data
        if data.provider == "telegram" and data.config_json:
            create_data = data.model_copy(update={"config_json": None})
        conn = await self.repo.create(user_id, create_data, display_name)
        return _safe_response(conn)

    async def update_connection(
        self, user_id: str, conn_id: str, data: IntegrationUpdate
    ) -> IntegrationResponse:
        conn = await self.repo.get_by_id(user_id, conn_id)
        if not conn:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Integration not found")
        update_data = data
        if conn.provider == "telegram" and data.config_json is not None:
            # Reject raw config_json on generic PATCH; use dedicated telegram config endpoint.
            update_data = data.model_copy(update={"config_json": None})
        updated = await self.repo.update(conn, update_data)
        return _safe_response(updated)

    async def delete_connection(self, user_id: str, conn_id: str) -> None:
        conn = await self.repo.get_by_id(user_id, conn_id)
        if not conn:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Integration not found")
        await self.repo.delete(conn)

    async def sync_connection(self, user_id: str, conn_id: str) -> IntegrationSyncResponse:
        conn = await self.repo.get_by_id(user_id, conn_id)
        if not conn:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Integration not found")
        if not conn.enabled:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Integration is disabled")
        now = datetime.now(timezone.utc)
        conn.last_sync_at = now
        conn.status = "synced"
        await self.repo.update(conn, IntegrationUpdate())
        return IntegrationSyncResponse(
            provider=conn.provider,
            status="stub_sync",
            message=f"Stub sync completed for {conn.provider}. Configure OAuth credentials for live sync.",
            synced_at=now,
        )

    async def get_or_create_telegram(self, user_id: str):
        conn = await self.repo.get_by_provider(user_id, "telegram")
        if conn is not None:
            return conn
        return await self.repo.create(
            user_id,
            IntegrationCreate(provider="telegram", enabled=False),
            "Telegram",
        )

    async def get_telegram_status(self, user_id: str) -> TelegramConfigStatus:
        conn = await self.get_or_create_telegram(user_id)
        masked = mask_config(conn.config_json)
        prefs = parse_preferences(conn.config_json)
        webhook_secret = getattr(conn, "webhook_secret", None)
        return TelegramConfigStatus(
            connection_id=conn.id,
            enabled=conn.enabled,
            status=conn.status,
            configured=masked.configured,
            bot_token_masked=masked.bot_token_masked,
            chat_id=masked.chat_id,
            last_sync_at=conn.last_sync_at,
            last_digest_at=getattr(conn, "last_digest_at", None),
            notify_on=prefs.notify_on,
            digest_enabled=prefs.digest_enabled,
            digest_time=prefs.digest_time,
            digest_frequency=prefs.digest_frequency,
            digest_weekday=prefs.digest_weekday,
            timezone=prefs.timezone,
            webhook_configured=bool(webhook_secret),
            webhook_url=None,
        )

    async def save_telegram_config(self, user_id: str, data: TelegramConfigUpdate) -> TelegramConfigStatus:
        conn = await self.get_or_create_telegram(user_id)
        has_secret = data.bot_token is not None or data.chat_id is not None
        has_prefs = any(
            v is not None
            for v in (
                data.notify_on,
                data.digest_enabled,
                data.digest_time,
                data.digest_frequency,
                data.digest_weekday,
                data.timezone,
            )
        )
        if data.enabled is None and not has_secret and not has_prefs:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")

        new_json = serialize_config(
            bot_token=data.bot_token,
            chat_id=data.chat_id,
            existing_json=conn.config_json,
            notify_on=data.notify_on,
            digest_enabled=data.digest_enabled,
            digest_time=data.digest_time,
            digest_frequency=data.digest_frequency,
            digest_weekday=data.digest_weekday,
            timezone=data.timezone,
        )

        update = IntegrationUpdate(config_json=new_json)
        if data.enabled is not None:
            update.enabled = data.enabled
        elif parse_config(new_json) is not None:
            # Auto-enable when credentials become complete unless explicitly disabled
            update.enabled = True

        updated = await self.repo.update(conn, update)
        if parse_config(updated.config_json) is not None and updated.enabled:
            updated.status = "connected"
            await self.repo.db.flush()

        # Keep per-user digest cron in sync with preferences
        try:
            from app.modules.integrations.scheduler import sync_user_digest_job

            sync_user_digest_job(user_id, parse_preferences(updated.config_json), enabled=updated.enabled)
        except Exception:
            logger.exception("Failed to sync digest job for user=%s", user_id)

        return await self.get_telegram_status(user_id)

    async def test_connection(self, user_id: str, conn_id: str) -> TelegramTestResponse:
        conn = await self.repo.get_by_id(user_id, conn_id)
        if not conn:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Integration not found")
        if conn.provider != "telegram":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Test is only supported for Telegram")

        cfg = parse_config(conn.config_json)
        if cfg is None:
            return TelegramTestResponse(ok=False, detail="Telegram not configured")

        client = TelegramClient(cfg.bot_token)
        try:
            me = await client.get_me()
            username = me.get("username")
            from app.modules.integrations.telegram_templates import test_connection_message

            await client.send_message(
                cfg.chat_id,
                test_connection_message(),
                parse_mode="HTML",
            )
            now = datetime.now(timezone.utc)
            conn.last_sync_at = now
            conn.status = "connected"
            await self.repo.db.flush()
            return TelegramTestResponse(
                ok=True,
                detail="Test message sent",
                bot_username=str(username) if username else None,
            )
        except TelegramClientError as exc:
            conn.status = "error"
            await self.repo.db.flush()
            return TelegramTestResponse(ok=False, detail=str(exc) or "Telegram test failed")

    async def detect_chat_id(
        self,
        user_id: str,
        conn_id: str,
        bot_token_override: str | None = None,
    ) -> DetectChatIdResponse:
        conn = await self.repo.get_by_id(user_id, conn_id)
        if not conn:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Integration not found")
        if conn.provider != "telegram":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Detect chat id is only for Telegram")

        token = (bot_token_override or "").strip()
        if not token:
            cfg = parse_config(conn.config_json)
            if cfg is None:
                return DetectChatIdResponse(
                    candidates=[],
                    detail="Provide a bot token or save one first, then message the bot.",
                )
            token = cfg.bot_token

        client = TelegramClient(token)
        try:
            updates = await client.get_updates(limit=50)
        except TelegramClientError as exc:
            return DetectChatIdResponse(candidates=[], detail=str(exc) or "Failed to fetch updates")

        seen: dict[str, ChatCandidate] = {}
        for update in updates:
            message = update.get("message") or update.get("channel_post") or {}
            chat = message.get("chat") if isinstance(message, dict) else None
            if not isinstance(chat, dict) or chat.get("id") is None:
                continue
            chat_id = str(chat["id"])
            if chat_id in seen:
                continue
            title = chat.get("title") or " ".join(
                p for p in [chat.get("first_name"), chat.get("last_name")] if p
            ) or None
            seen[chat_id] = ChatCandidate(
                chat_id=chat_id,
                type=chat.get("type"),
                title=title,
                username=chat.get("username"),
            )

        candidates = list(seen.values())
        if not candidates:
            return DetectChatIdResponse(
                candidates=[],
                detail="No chats found. Open your bot in Telegram, press Start (or send a message), then try again.",
            )
        return DetectChatIdResponse(
            candidates=candidates,
            detail=f"Found {len(candidates)} chat(s).",
        )
