"""BYOK config, connection test and provider access for the per-user Google Maps key (Wordnik pattern)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.core.timezone import utc_now
from app.modules.integrations.common import last_test_ok
from app.modules.integrations.models import IntegrationConnection
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    GoogleMapsConfigStatus,
    GoogleMapsConfigUpdate,
    GoogleMapsTestResponse,
    IntegrationUpdate,
)
from app.modules.travel.maps.config import load_api_key, mask_key, serialize_config
from app.modules.travel.maps.errors import MapsError
from app.modules.travel.maps.google import GoogleMapsProvider
from app.modules.travel.maps.types import Feature, Sku
from app.modules.travel.services.usage_service import UsageService

PROVIDER = "google_maps"
DISPLAY_NAME = "Google Maps"
# A fixed, well-known point: the test is one reverse-geocode request, tracked like any other.
_TEST_POINT = (28.6139, 77.2090)


class GoogleMapsIntegrationService:
    def __init__(self, db: AsyncSession):
        self.repo = IntegrationRepository(db)
        self.usage = UsageService(db)

    async def _get_or_create(self, user_id: str) -> IntegrationConnection:
        return await self.repo.get_or_create(user_id, PROVIDER, DISPLAY_NAME)

    async def provider_for(self, user_id: str) -> GoogleMapsProvider | None:
        """A provider for the user's enabled key, or None when not connected."""
        conn = await self.repo.get_by_provider(user_id, PROVIDER)
        if conn is None or not conn.enabled:
            return None
        key = load_api_key(conn.config_json)
        return GoogleMapsProvider(key) if key else None

    async def status(self, user_id: str) -> GoogleMapsConfigStatus:
        conn = await self._get_or_create(user_id)
        key = load_api_key(conn.config_json)
        return GoogleMapsConfigStatus(
            connection_id=conn.id,
            enabled=conn.enabled,
            status=conn.status,
            configured=bool(key),
            api_key_masked=mask_key(key),
            last_tested_at=conn.last_sync_at,
            last_test_ok=last_test_ok(conn.status),
        )

    async def save(self, user_id: str, data: GoogleMapsConfigUpdate) -> GoogleMapsConfigStatus:
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
            updated.status = "disconnected"
            updated.last_sync_at = None
            await self.repo.db.flush()
        return await self.status(user_id)

    async def test(self, user_id: str) -> GoogleMapsTestResponse:
        conn = await self._get_or_create(user_id)
        key = load_api_key(conn.config_json)
        if not key:
            return GoogleMapsTestResponse(ok=False, detail="Google Maps API key not configured")
        try:
            await GoogleMapsProvider(key).reverse_geocode(*_TEST_POINT)
        except MapsError as exc:
            conn.status = "error"
            await self.repo.db.flush()
            await self.usage.record(user_id, Sku.GEOCODING, Feature.CONNECTION_TEST, "error")
            return GoogleMapsTestResponse(ok=False, detail=str(exc))
        conn.status = "connected"
        conn.last_sync_at = utc_now()
        await self.repo.db.flush()
        await self.usage.record(user_id, Sku.GEOCODING, Feature.CONNECTION_TEST, "ok")
        return GoogleMapsTestResponse(ok=True, detail="Google Maps API key verified")
