from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.models import INTEGRATION_PROVIDERS
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    IntegrationCreate,
    IntegrationProviderInfo,
    IntegrationResponse,
    IntegrationSyncResponse,
    IntegrationUpdate,
)

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


class IntegrationService:
    def __init__(self, db: AsyncSession):
        self.repo = IntegrationRepository(db)

    async def list_connections(self, user_id: str) -> list[IntegrationResponse]:
        conns = await self.repo.list_connections(user_id)
        return [IntegrationResponse.model_validate(c) for c in conns]

    async def create_connection(self, user_id: str, data: IntegrationCreate) -> IntegrationResponse:
        if data.provider not in INTEGRATION_PROVIDERS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown provider: {data.provider}")
        existing = await self.repo.get_by_provider(user_id, data.provider)
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, "Integration already exists for this provider")
        catalog = next((p for p in PROVIDER_CATALOG if p.provider == data.provider), None)
        display_name = data.display_name or (catalog.display_name if catalog else data.provider)
        conn = await self.repo.create(user_id, data, display_name)
        return IntegrationResponse.model_validate(conn)

    async def update_connection(
        self, user_id: str, conn_id: str, data: IntegrationUpdate
    ) -> IntegrationResponse:
        conn = await self.repo.get_by_id(user_id, conn_id)
        if not conn:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Integration not found")
        updated = await self.repo.update(conn, data)
        return IntegrationResponse.model_validate(updated)

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
        now = datetime.now(UTC)
        conn.last_sync_at = now
        conn.status = "synced"
        await self.repo.update(conn, IntegrationUpdate())
        return IntegrationSyncResponse(
            provider=conn.provider,
            status="stub_sync",
            message=f"Stub sync completed for {conn.provider}. Configure OAuth credentials for live sync.",
            synced_at=now,
        )
