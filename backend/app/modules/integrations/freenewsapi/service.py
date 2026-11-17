"""BYOK config, connection test and key resolution for the FreeNewsAPI news provider (Wordnik pattern)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import BadRequestError
from app.core.timezone import utc_now
from app.modules.integrations.common import (
    last_test_ok,
    load_api_key,
    mask_secret,
    serialize_api_key_config,
)
from app.modules.integrations.models import IntegrationConnection
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    IntegrationUpdate,
    NewsProviderConfigStatus,
    NewsProviderConfigUpdate,
    NewsProviderTestResponse,
)
from app.modules.news.client import FreeNewsClient, NewsApiError

PROVIDER = "freenewsapi"
DISPLAY_NAME = "FreeNewsAPI"


class FreeNewsApiIntegrationService:
    def __init__(self, db: AsyncSession):
        self.repo = IntegrationRepository(db)

    async def _get_or_create(self, user_id: str) -> IntegrationConnection:
        return await self.repo.get_or_create(user_id, PROVIDER, DISPLAY_NAME)

    async def api_key_for(self, user_id: str | None, settings: Settings) -> str:
        """The user's enabled key, else the server-wide fallback, else "" (not connected)."""
        if user_id is not None:
            conn = await self.repo.get_by_provider(user_id, PROVIDER)
            if conn is not None and conn.enabled:
                key = load_api_key(conn.config_json, label=PROVIDER)
                if key:
                    return key
        return settings.freenews_api_key.strip()

    async def status(self, user_id: str) -> NewsProviderConfigStatus:
        conn = await self._get_or_create(user_id)
        key = load_api_key(conn.config_json, label=PROVIDER)
        return NewsProviderConfigStatus(
            connection_id=conn.id,
            enabled=conn.enabled,
            status=conn.status,
            configured=bool(key),
            api_key_masked=mask_secret(key) if key else None,
            last_tested_at=conn.last_sync_at,
            last_test_ok=last_test_ok(conn.status),
        )

    async def save(self, user_id: str, data: NewsProviderConfigUpdate) -> NewsProviderConfigStatus:
        if not data.model_fields_set:
            raise BadRequestError("No fields to update")
        conn = await self._get_or_create(user_id)
        new_key = (data.api_key or "").strip()
        update = IntegrationUpdate(
            config_json=serialize_api_key_config(
                existing_json=conn.config_json, api_key=new_key or None, label=PROVIDER
            )
        )
        if data.enabled is not None:
            update.enabled = data.enabled
        elif new_key:
            update.enabled = True
        updated = await self.repo.update(conn, update)
        if new_key:
            # A new key has not been verified yet.
            updated.status = "disconnected"
            updated.last_sync_at = None
            await self.repo.db.flush()
        return await self.status(user_id)

    async def test(self, user_id: str) -> NewsProviderTestResponse:
        conn = await self._get_or_create(user_id)
        key = load_api_key(conn.config_json, label=PROVIDER)
        if not key:
            return NewsProviderTestResponse(ok=False, detail="FreeNewsAPI key not configured")
        try:
            await FreeNewsClient(key).search({"size": 1})
        except NewsApiError as exc:
            conn.status = "error"
            await self.repo.db.flush()
            return NewsProviderTestResponse(ok=False, detail=str(exc))
        conn.status = "connected"
        conn.last_sync_at = utc_now()
        await self.repo.db.flush()
        return NewsProviderTestResponse(ok=True, detail="FreeNewsAPI key verified")
