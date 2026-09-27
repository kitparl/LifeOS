"""Centralised Google Maps usage tracking and application-level cost protection (spec §26–§29).

Every Google request made by Travel is recorded here by `MapsGateway` (or the key test), and every
request is checked here first. Prices come only from the user's `map_pricing_configurations` rows.
All figures are estimates; Google Cloud billing is authoritative.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.core.timezone import as_utc, utc_now
from app.modules.travel.maps.pricing_defaults import DEFAULT_FX_RATES, DEFAULT_PRICING
from app.modules.travel.maps.types import ESSENTIAL_SKUS, SKU_API, Sku
from app.modules.travel.models import MapPricingConfiguration, MapsUsageEvent, TravelMapsSettings
from app.modules.travel.repository.usage import UsageRepository
from app.modules.travel.schemas.usage import (
    BudgetStatus,
    MapsSettingsOut,
    MapsSettingsUpdate,
    MapsStatus,
    PricingRow,
    PricingUpdate,
    SkuUsage,
    UsageLevel,
    UsageSummary,
)

# Spec §28 defaults: (threshold percent, level), highest first.
THRESHOLDS: tuple[tuple[float, UsageLevel], ...] = (
    (100, "limit"),
    (95, "critical"),
    (85, "high"),
    (70, "warning"),
    (50, "info"),
)
PRICING_REVIEW_DAYS = 90
_CENT = Decimal("0.000001")


# ---- pure rules (property-tested) -------------------------------------------------------------


def usage_level(pct: float | None) -> UsageLevel:
    if pct is None:
        return "ok"
    for threshold, level in THRESHOLDS:
        if pct >= threshold:
            return level
    return "ok"


def marginal_cost_usd(prior_units: int, units: int, free_units: int, price_per_1000: Decimal) -> Decimal:
    """Cost of `units` more requests after `prior_units` this month; the free allowance is used first."""
    billable_after = max(0, prior_units + units - free_units)
    billable_before = max(0, prior_units - free_units)
    return (Decimal(billable_after - billable_before) * price_per_1000 / 1000).quantize(_CENT, ROUND_HALF_UP)


def to_usd(amount: Decimal, currency: str, fx_rates: dict[str, float]) -> Decimal | None:
    """`fx_rates` holds units of currency per 1 USD. None when the rate is unknown."""
    if currency == "USD":
        return amount
    rate = fx_rates.get(currency)
    return None if not rate else amount / Decimal(str(rate))


def from_usd(amount_usd: Decimal, currency: str, fx_rates: dict[str, float]) -> Decimal | None:
    if currency == "USD":
        return amount_usd
    rate = fx_rates.get(currency)
    return None if not rate else amount_usd * Decimal(str(rate))


def block_reason(
    *,
    protection_enabled: bool,
    stop_at_free_tier: bool,
    spent_usd: Decimal,
    budget_usd: Decimal | None,
    sku_units: int,
    free_units: int,
    essential: bool,
) -> str | None:
    """None to allow the request, else why cost protection refuses it (spec §29, requirements D-10).

    At the safety budget non-essential requests stop; an essential request (reverse geocode on a map
    tap) keeps working only while its own free allowance lasts, so it never adds cost past the budget.
    """
    if not protection_enabled:
        return None
    within_free = sku_units < free_units
    if stop_at_free_tier and not within_free:
        return "free_allowance_used"
    if budget_usd is not None and spent_usd >= budget_usd:
        return None if essential and within_free else "budget_reached"
    return None


def month_bounds(month: str | None, now: datetime) -> tuple[datetime, datetime, str]:
    """[start, end) of a UTC calendar month given as YYYY-MM (default: the current month)."""
    if month:
        try:
            year, mon = (int(p) for p in month.split("-"))
            start = now.replace(year=year, month=mon, day=1, hour=0, minute=0, second=0, microsecond=0)
        except ValueError as exc:
            raise BadRequestError("month must be YYYY-MM") from exc
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = (start + timedelta(days=32)).replace(day=1)
    return start, end, f"{start.year:04d}-{start.month:02d}"


def build_sku_usage(
    rows: Iterable[tuple[str, str, int, Decimal]], pricing: Iterable[MapPricingConfiguration]
) -> list[SkuUsage]:
    """Fold (sku, outcome, requests, cost) rows into one line per priced SKU."""
    by_sku: dict[str, dict[str, Decimal | int]] = {}
    for sku, outcome, requests, cost in rows:
        agg = by_sku.setdefault(sku, {"requests": 0, "blocked": 0, "cost": Decimal(0)})
        if outcome == "blocked":
            agg["blocked"] = int(agg["blocked"]) + requests
        elif outcome == "ok":
            agg["requests"] = int(agg["requests"]) + requests
        agg["cost"] = Decimal(agg["cost"]) + cost
    out: list[SkuUsage] = []
    for price in pricing:
        agg = by_sku.get(price.sku, {"requests": 0, "blocked": 0, "cost": Decimal(0)})
        requests = int(agg["requests"])
        pct = round(requests / price.free_monthly_units * 100, 1) if price.free_monthly_units else 0.0
        out.append(
            SkuUsage(
                sku=price.sku,
                label=price.label,
                requests=requests,
                blocked=int(agg["blocked"]),
                free_units=price.free_monthly_units,
                pct_of_free=pct,
                estimated_cost_usd=Decimal(agg["cost"]),
                level=usage_level(pct) if price.free_monthly_units else "ok",
            )
        )
    return out


# ---- service ---------------------------------------------------------------------------------


class UsageService:
    def __init__(self, db: AsyncSession):
        self.repo = UsageRepository(db)

    async def ensure_defaults(self, user_id: str) -> TravelMapsSettings:
        """Seed pricing rows and the settings row on first use (data, not code, from then on)."""
        existing = {p.sku for p in await self.repo.list_pricing(user_id)}
        missing = [
            MapPricingConfiguration(
                user_id=user_id, sku=sku.value, label=label, unit_price_usd_per_1000=price, free_monthly_units=free
            )
            for sku, label, price, free in DEFAULT_PRICING
            if sku.value not in existing
        ]
        if missing:
            await self.repo.add_pricing(missing)
        settings = await self.repo.get_settings(user_id)
        if settings is None:
            settings = await self.repo.add_settings(
                TravelMapsSettings(user_id=user_id, fx_rates=dict(DEFAULT_FX_RATES))
            )
        return settings

    async def _budget_usd(self, settings: TravelMapsSettings) -> Decimal | None:
        return to_usd(Decimal(settings.budget_amount), settings.budget_currency, settings.fx_rates or {})

    async def check(self, user_id: str, sku: Sku) -> str | None:
        """None when the request may go ahead, else the block reason."""
        settings = await self.ensure_defaults(user_id)
        if not settings.protection_enabled:
            return None
        start, _, _ = month_bounds(None, utc_now())
        pricing = await self.repo.get_pricing(user_id, sku.value)
        return block_reason(
            protection_enabled=True,
            stop_at_free_tier=settings.stop_at_free_tier,
            spent_usd=await self.repo.cost_since(user_id, start),
            budget_usd=await self._budget_usd(settings),
            sku_units=await self.repo.billable_units(user_id, sku.value, start),
            free_units=pricing.free_monthly_units if pricing and pricing.active else 0,
            essential=sku in ESSENTIAL_SKUS,
        )

    async def record(self, user_id: str, sku: Sku, feature: str, outcome: str, units: int = 1) -> None:
        cost = Decimal(0)
        if outcome == "ok":
            await self.ensure_defaults(user_id)
            pricing = await self.repo.get_pricing(user_id, sku.value)
            if pricing is not None and pricing.active:
                start, _, _ = month_bounds(None, utc_now())
                prior = await self.repo.billable_units(user_id, sku.value, start)
                cost = marginal_cost_usd(
                    prior, units, pricing.free_monthly_units, Decimal(pricing.unit_price_usd_per_1000)
                )
        await self.repo.add_event(
            MapsUsageEvent(
                user_id=user_id,
                api=SKU_API[sku],
                sku=sku.value,
                feature=str(feature),
                request_count=units,
                estimated_cost_usd=cost,
                outcome=outcome,
            )
        )

    async def _budget_status(self, settings: TravelMapsSettings, spent_usd: Decimal) -> BudgetStatus:
        fx = settings.fx_rates or {}
        budget_usd = await self._budget_usd(settings)
        pct = float(spent_usd / budget_usd * 100) if budget_usd else None
        spent_local = from_usd(spent_usd, settings.budget_currency, fx)
        warning_usd = to_usd(Decimal(settings.warning_amount), settings.budget_currency, fx)
        level = usage_level(pct)
        if level == "ok" and warning_usd is not None and warning_usd > 0 and spent_usd >= warning_usd:
            level = "warning"
        blocked = bool(settings.protection_enabled and budget_usd is not None and spent_usd >= budget_usd)
        return BudgetStatus(
            protection_enabled=settings.protection_enabled,
            budget_amount=Decimal(settings.budget_amount),
            warning_amount=Decimal(settings.warning_amount),
            currency=settings.budget_currency,
            spent_usd=spent_usd,
            spent_in_budget_currency=spent_local.quantize(Decimal("0.01")) if spent_local is not None else None,
            pct_of_budget=round(pct, 1) if pct is not None else None,
            level=level,
            non_essential_blocked=blocked,
        )

    async def month_summary(self, user_id: str, month: str | None) -> UsageSummary:
        settings = await self.ensure_defaults(user_id)
        now = utc_now()
        start, end, label = month_bounds(month, now)
        rows = await self.repo.summary_rows(user_id, start, end)
        pricing = await self.repo.list_pricing(user_id)
        skus = build_sku_usage(rows, pricing)
        total = sum((s.estimated_cost_usd for s in skus), Decimal(0))
        reviewed = settings.pricing_last_reviewed_at
        return UsageSummary(
            month=label,
            skus=skus,
            total_estimated_cost_usd=total,
            budget=await self._budget_status(settings, await self.repo.cost_since(user_id, start)),
            fx_rates=settings.fx_rates or {},
            pricing_last_reviewed_at=reviewed,
            pricing_review_due=reviewed is None or now - as_utc(reviewed) > timedelta(days=PRICING_REVIEW_DAYS),
        )

    async def maps_status(self, user_id: str, configured: bool) -> MapsStatus:
        settings = await self.ensure_defaults(user_id)
        start, _, _ = month_bounds(None, utc_now())
        budget = await self._budget_status(settings, await self.repo.cost_since(user_id, start))
        return MapsStatus(configured=configured, level=budget.level, non_essential_blocked=budget.non_essential_blocked)

    async def get_settings(self, user_id: str) -> MapsSettingsOut:
        return _settings_out(await self.ensure_defaults(user_id))

    async def update_settings(self, user_id: str, data: MapsSettingsUpdate) -> MapsSettingsOut:
        settings = await self.ensure_defaults(user_id)
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in fields.items():
            setattr(settings, key, value)
        fx = settings.fx_rates or {}
        if settings.budget_currency != "USD" and settings.budget_currency not in fx:
            raise BadRequestError(f"Add a USD→{settings.budget_currency} rate before using it for the budget")
        if Decimal(settings.warning_amount) > Decimal(settings.budget_amount):
            raise BadRequestError("Warning amount must not exceed the budget")
        await self.repo.flush()
        return _settings_out(settings)

    async def list_pricing(self, user_id: str) -> list[PricingRow]:
        await self.ensure_defaults(user_id)
        return [PricingRow.model_validate(p) for p in await self.repo.list_pricing(user_id)]

    async def update_pricing(self, user_id: str, data: PricingUpdate) -> list[PricingRow]:
        settings = await self.ensure_defaults(user_id)
        by_sku = {p.sku: p for p in await self.repo.list_pricing(user_id)}
        for row in data.rows:
            target = by_sku.get(row.sku)
            if target is None:
                raise BadRequestError(f"Unknown sku '{row.sku}'")
            target.unit_price_usd_per_1000 = row.unit_price_usd_per_1000
            target.free_monthly_units = row.free_monthly_units
            target.active = row.active
        settings.pricing_last_reviewed_at = utc_now()
        await self.repo.flush()
        return [PricingRow.model_validate(p) for p in by_sku.values()]


def _settings_out(settings: TravelMapsSettings) -> MapsSettingsOut:
    return MapsSettingsOut(
        protection_enabled=settings.protection_enabled,
        budget_amount=Decimal(settings.budget_amount),
        warning_amount=Decimal(settings.warning_amount),
        budget_currency=settings.budget_currency,
        stop_at_free_tier=settings.stop_at_free_tier,
        fx_rates=settings.fx_rates or {},
        pricing_last_reviewed_at=settings.pricing_last_reviewed_at,
    )
