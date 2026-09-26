"""BYOK config, connection test, and credential access for the Wordnik integration."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.core.timezone import utc_now, utc_today
from app.modules.integrations.common import last_test_ok
from app.modules.integrations.models import IntegrationConnection
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    IntegrationUpdate,
    WordnikConfigStatus,
    WordnikConfigUpdate,
    WordnikTestResponse,
)
from app.modules.integrations.wordnik.client import WordnikClient, WordnikError
from app.modules.integrations.wordnik.config import (
    WordnikUsage,
    load_config,
    mask_key,
    parse_config,
    serialize_config,
    usage_remaining_pct,
    with_usage,
)

PROVIDER = "wordnik"
DISPLAY_NAME = "Wordnik"


class WordnikIntegrationService:
    def __init__(self, db: AsyncSession):
        self.repo = IntegrationRepository(db)

    async def _get_or_create(self, user_id: str) -> IntegrationConnection:
        return await self.repo.get_or_create(user_id, PROVIDER, DISPLAY_NAME)

    async def client_for(self, user_id: str) -> WordnikClient | None:
        """A client for the user's enabled Wordnik key, or None when not connected."""
        conn = await self.repo.get_by_provider(user_id, PROVIDER)
        if conn is None or not conn.enabled:
            return None
        cfg = parse_config(conn.config_json)
        return WordnikClient(cfg.api_key) if cfg is not None else None

    async def usage_pct(self, user_id: str) -> int | None:
        conn = await self.repo.get_by_provider(user_id, PROVIDER)
        if conn is None:
            return None
        return usage_remaining_pct(load_config(conn.config_json).usage, utc_now())

    async def record_usage(self, user_id: str, usage: WordnikUsage | None) -> int | None:
        """Persist the latest rate-limit reading; returns the resulting percent (None when unknown)."""
        if usage is None:
            return await self.usage_pct(user_id)
        conn = await self.repo.get_by_provider(user_id, PROVIDER)
        if conn is not None:
            conn.config_json = with_usage(conn.config_json, usage)
            await self.repo.db.flush()
        return usage_remaining_pct(usage, utc_now())

    async def status(self, user_id: str) -> WordnikConfigStatus:
        conn = await self._get_or_create(user_id)
        cfg = load_config(conn.config_json)
        return WordnikConfigStatus(
            connection_id=conn.id,
            enabled=conn.enabled,
            status=conn.status,
            configured=bool(cfg.api_key),
            api_key_masked=mask_key(cfg.api_key),
            last_tested_at=conn.last_sync_at,
            last_test_ok=last_test_ok(conn.status),
            usage_remaining_pct=usage_remaining_pct(cfg.usage, utc_now()),
        )

    async def save(self, user_id: str, data: WordnikConfigUpdate) -> WordnikConfigStatus:
        if not data.model_fields_set:
            raise BadRequestError("No fields to update")
        conn = await self._get_or_create(user_id)
        new_key = (data.api_key or "").strip()
        update = IntegrationUpdate(
            config_json=serialize_config(existing_json=conn.config_json, api_key=new_key or None)
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

    async def test(self, user_id: str) -> WordnikTestResponse:
        conn = await self._get_or_create(user_id)
        cfg = parse_config(conn.config_json)
        if cfg is None:
            return WordnikTestResponse(ok=False, detail="Wordnik API key not configured")
        client = WordnikClient(cfg.api_key)
        try:
            await client.word_of_the_day(utc_today())
        except WordnikError as exc:
            conn.status = "error"
            await self.repo.db.flush()
            await self.record_usage(user_id, client.last_usage)
            return WordnikTestResponse(ok=False, detail=str(exc))
        conn.status = "connected"
        conn.last_sync_at = utc_now()
        await self.repo.db.flush()
        await self.record_usage(user_id, client.last_usage)
        return WordnikTestResponse(ok=True, detail="Wordnik API key verified")
