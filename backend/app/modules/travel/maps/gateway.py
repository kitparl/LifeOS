"""`MapsGateway` — the one door every Google Maps request goes through (spec §24, §26, §38).

Order per call: per-user rate limit -> resolve the user's key -> cost protection check -> provider
call -> usage event. Nothing is sent to Google without a recorded event, and a blocked call is
recorded (cost 0) without reaching Google. Callers catch `MapsError` and fall back.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TooManyRequestsError
from app.core.rate_limit import SlidingWindowLimiter
from app.modules.travel.maps.errors import MapsBlocked, MapsError, MapsNotConfigured
from app.modules.travel.maps.integration_service import GoogleMapsIntegrationService
from app.modules.travel.maps.provider import MapsProvider
from app.modules.travel.maps.types import Feature, Sku
from app.modules.travel.services.usage_service import UsageService

T = TypeVar("T")

# Misuse guard (SECURITY-11): a script hammering search cannot burn the user's key.
_limiter = SlidingWindowLimiter(limit=60, window_seconds=60)


def reset_limiter() -> None:
    _limiter.reset()


class MapsGateway:
    def __init__(self, db: AsyncSession):
        self.usage = UsageService(db)
        self.integration = GoogleMapsIntegrationService(db)

    async def is_configured(self, user_id: str) -> bool:
        return await self.integration.provider_for(user_id) is not None

    async def call(
        self,
        user_id: str,
        sku: Sku,
        feature: Feature,
        operation: Callable[[MapsProvider], Awaitable[T]],
        units: int = 1,
    ) -> T:
        if not _limiter.hit(user_id):
            raise TooManyRequestsError("Too many map lookups; slow down a little")
        provider = await self.integration.provider_for(user_id)
        if provider is None:
            raise MapsNotConfigured("Google Maps key not configured")
        reason = await self.usage.check(user_id, sku)
        if reason is not None:
            await self.usage.record(user_id, sku, feature, "blocked", units)
            raise MapsBlocked(reason)
        try:
            result = await operation(provider)
        except MapsError:
            await self.usage.record(user_id, sku, feature, "error", units)
            raise
        await self.usage.record(user_id, sku, feature, "ok", units)
        return result
