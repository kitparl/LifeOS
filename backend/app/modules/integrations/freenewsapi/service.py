"""BYOK config (several keys, failover order), connection test and key resolution for the FreeNewsAPI news provider."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.timezone import utc_now
from app.modules.integrations.common import last_test_ok, load_api_keys, mask_secret, serialize_api_keys
from app.modules.integrations.models import IntegrationConnection
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    IntegrationUpdate,
    NewsProviderConfigStatus,
    NewsProviderConfigUpdate,
    NewsProviderKeyStatus,
    NewsProviderTestResponse,
)
from app.modules.news import key_pool
from app.modules.news.client import FreeNewsClient, NewsApiError

PROVIDER = "freenewsapi"
DISPLAY_NAME = "FreeNewsAPI"
MAX_KEYS = 5


class FreeNewsApiIntegrationService:
    def __init__(self, db: AsyncSession):
        self.repo = IntegrationRepository(db)

    async def _get_or_create(self, user_id: str) -> IntegrationConnection:
        return await self.repo.get_or_create(user_id, PROVIDER, DISPLAY_NAME)

    async def api_keys_for(self, user_id: str | None, settings: Settings) -> list[str]:
        """Keys to try, in order: the user's enabled keys, then the server-wide fallback. Empty when not connected."""
        keys: list[str] = []
        if user_id is not None:
            conn = await self.repo.get_by_provider(user_id, PROVIDER)
            if conn is not None and conn.enabled:
                keys = load_api_keys(conn.config_json, label=PROVIDER)
        fallback = settings.freenews_api_key.strip()
        if fallback and fallback not in keys:
            keys.append(fallback)
        return keys

    async def status(self, user_id: str) -> NewsProviderConfigStatus:
        conn = await self._get_or_create(user_id)
        keys = load_api_keys(conn.config_json, label=PROVIDER)
        return NewsProviderConfigStatus(
            connection_id=conn.id,
            enabled=conn.enabled,
            status=conn.status,
            configured=bool(keys),
            keys=[self._key_status(k) for k in keys],
            last_tested_at=conn.last_sync_at,
            last_test_ok=last_test_ok(conn.status),
        )

    @staticmethod
    def _key_status(key: str) -> NewsProviderKeyStatus:
        parked = key_pool.parked(key)
        return NewsProviderKeyStatus(
            id=key_pool.fingerprint(key),
            masked=mask_secret(key),
            state=parked.state if parked else "ok",
            retry_at=parked.until if parked else None,
        )

    async def save(self, user_id: str, data: NewsProviderConfigUpdate) -> NewsProviderConfigStatus:
        """Add a key (a non-blank `api_key`, appended last) and/or toggle `enabled`."""
        if not data.model_fields_set:
            raise BadRequestError("No fields to update")
        conn = await self._get_or_create(user_id)
        new_key = (data.api_key or "").strip()
        update = IntegrationUpdate()
        keys = load_api_keys(conn.config_json, label=PROVIDER)
        key_added = bool(new_key) and new_key not in keys
        if key_added:
            if len(keys) >= MAX_KEYS:
                raise BadRequestError(f"You can add up to {MAX_KEYS} keys")
            update.config_json = serialize_api_keys([*keys, new_key])
        if data.enabled is not None:
            update.enabled = data.enabled
        elif new_key:
            update.enabled = True
        updated = await self.repo.update(conn, update)
        if key_added:
            # A new key has not been verified yet.
            updated.status = "disconnected"
            updated.last_sync_at = None
            await self.repo.db.flush()
        return await self.status(user_id)

    async def remove_key(self, user_id: str, key_id: str) -> NewsProviderConfigStatus:
        conn = await self._get_or_create(user_id)
        keys = load_api_keys(conn.config_json, label=PROVIDER)
        remaining = [k for k in keys if key_pool.fingerprint(k) != key_id]
        if len(remaining) == len(keys):
            raise NotFoundError("Key not found")
        await self.repo.update(conn, IntegrationUpdate(config_json=serialize_api_keys(remaining)))
        return await self.status(user_id)

    async def test(self, user_id: str) -> NewsProviderTestResponse:
        """Verify every stored key with one search each (this also re-evaluates keys that were parked)."""
        conn = await self._get_or_create(user_id)
        keys = load_api_keys(conn.config_json, label=PROVIDER)
        if not keys:
            return NewsProviderTestResponse(ok=False, detail="FreeNewsAPI key not configured")
        failures: list[str] = []
        for key in keys:
            key_pool.clear(key)
            try:
                await FreeNewsClient([key]).search({"size": 1})
            except NewsApiError as exc:
                failures.append(f"{mask_secret(key)}: {exc}")
        working = len(keys) - len(failures)
        if working:
            conn.status = "connected"
            conn.last_sync_at = utc_now()
        else:
            conn.status = "error"
        await self.repo.db.flush()
        if not failures:
            return NewsProviderTestResponse(
                ok=True, detail="FreeNewsAPI key verified" if len(keys) == 1 else f"All {len(keys)} keys verified"
            )
        return NewsProviderTestResponse(
            ok=working > 0, detail=(f"{working} of {len(keys)} keys working. " if working else "") + " ".join(failures)
        )
