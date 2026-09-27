from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.travel.models import MapPricingConfiguration, MapsUsageEvent, TravelMapsSettings


class UsageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_event(self, event: MapsUsageEvent) -> None:
        self.db.add(event)
        await self.db.flush()

    async def billable_units(self, user_id: str, sku: str, since: datetime) -> int:
        """Requests Google bills for (outcome ok) this period."""
        total = await self.db.scalar(
            select(func.coalesce(func.sum(MapsUsageEvent.request_count), 0)).where(
                MapsUsageEvent.user_id == user_id,
                MapsUsageEvent.sku == sku,
                MapsUsageEvent.outcome == "ok",
                MapsUsageEvent.created_at >= since,
            )
        )
        return int(total or 0)

    async def cost_since(self, user_id: str, since: datetime) -> Decimal:
        total = await self.db.scalar(
            select(func.coalesce(func.sum(MapsUsageEvent.estimated_cost_usd), 0)).where(
                MapsUsageEvent.user_id == user_id, MapsUsageEvent.created_at >= since
            )
        )
        return Decimal(str(total or 0))

    async def summary_rows(self, user_id: str, start: datetime, end: datetime) -> list[tuple[str, str, int, Decimal]]:
        """(sku, outcome, requests, cost) grouped for one period — one indexed scan."""
        result = await self.db.execute(
            select(
                MapsUsageEvent.sku,
                MapsUsageEvent.outcome,
                func.sum(MapsUsageEvent.request_count),
                func.sum(MapsUsageEvent.estimated_cost_usd),
            )
            .where(
                MapsUsageEvent.user_id == user_id,
                MapsUsageEvent.created_at >= start,
                MapsUsageEvent.created_at < end,
            )
            .group_by(MapsUsageEvent.sku, MapsUsageEvent.outcome)
        )
        return [(sku, outcome, int(n or 0), Decimal(str(cost or 0))) for sku, outcome, n, cost in result.all()]

    async def list_pricing(self, user_id: str) -> list[MapPricingConfiguration]:
        result = await self.db.execute(
            select(MapPricingConfiguration)
            .where(MapPricingConfiguration.user_id == user_id)
            .order_by(MapPricingConfiguration.label)
        )
        return list(result.scalars().all())

    async def get_pricing(self, user_id: str, sku: str) -> MapPricingConfiguration | None:
        result = await self.db.execute(
            select(MapPricingConfiguration).where(
                MapPricingConfiguration.user_id == user_id, MapPricingConfiguration.sku == sku
            )
        )
        return result.scalar_one_or_none()

    async def add_pricing(self, rows: list[MapPricingConfiguration]) -> None:
        self.db.add_all(rows)
        await self.db.flush()

    async def get_settings(self, user_id: str) -> TravelMapsSettings | None:
        result = await self.db.execute(select(TravelMapsSettings).where(TravelMapsSettings.user_id == user_id))
        return result.scalar_one_or_none()

    async def add_settings(self, settings: TravelMapsSettings) -> TravelMapsSettings:
        self.db.add(settings)
        await self.db.flush()
        await self.db.refresh(settings)
        return settings

    async def flush(self) -> None:
        await self.db.flush()
