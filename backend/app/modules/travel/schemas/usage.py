from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

UsageLevel = Literal["ok", "info", "warning", "high", "critical", "limit"]
CurrencyCode = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]


class SkuUsage(BaseModel):
    sku: str
    label: str
    requests: int
    blocked: int
    free_units: int
    pct_of_free: float
    estimated_cost_usd: Decimal
    level: UsageLevel


class BudgetStatus(BaseModel):
    protection_enabled: bool
    budget_amount: Decimal
    warning_amount: Decimal
    currency: str
    spent_usd: Decimal
    spent_in_budget_currency: Decimal | None
    pct_of_budget: float | None
    level: UsageLevel
    non_essential_blocked: bool


class UsageSummary(BaseModel):
    month: str
    skus: list[SkuUsage]
    total_estimated_cost_usd: Decimal
    budget: BudgetStatus
    fx_rates: dict[str, float]
    pricing_last_reviewed_at: datetime | None
    pricing_review_due: bool


class MapsSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    protection_enabled: bool
    budget_amount: Decimal
    warning_amount: Decimal
    budget_currency: str
    stop_at_free_tier: bool
    fx_rates: dict[str, float]
    pricing_last_reviewed_at: datetime | None


class MapsSettingsUpdate(BaseModel):
    protection_enabled: bool | None = None
    budget_amount: Decimal | None = Field(default=None, ge=0, le=10_000_000, decimal_places=2)
    warning_amount: Decimal | None = Field(default=None, ge=0, le=10_000_000, decimal_places=2)
    budget_currency: CurrencyCode | None = None
    stop_at_free_tier: bool | None = None
    fx_rates: dict[CurrencyCode, Annotated[float, Field(gt=0, le=1_000_000)]] | None = Field(
        default=None, max_length=20
    )


class PricingRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sku: str
    label: str
    unit_price_usd_per_1000: Decimal
    free_monthly_units: int
    active: bool


class PricingRowUpdate(BaseModel):
    sku: str = Field(min_length=1, max_length=32)
    unit_price_usd_per_1000: Decimal = Field(ge=0, le=10_000, decimal_places=4)
    free_monthly_units: int = Field(ge=0, le=100_000_000)
    active: bool = True


class PricingUpdate(BaseModel):
    rows: list[PricingRowUpdate] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def _unique(self) -> PricingUpdate:
        skus = [r.sku for r in self.rows]
        if len(skus) != len(set(skus)):
            raise ValueError("duplicate sku")
        return self


class MapsStatus(BaseModel):
    """What the Map tab needs to decide between Google lookups and the coordinates-only fallback."""

    configured: bool
    level: UsageLevel
    non_essential_blocked: bool
