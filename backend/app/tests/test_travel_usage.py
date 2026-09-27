"""Travel OS U5 — maps usage dashboard, budgets in the user's currency, pricing ownership."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.tests.travel_support import auth as _auth
from app.tests.travel_support import connect_google as _connect_google

BASE = "/api/v1/travel"


@pytest.mark.asyncio
async def test_defaults_are_seeded_as_data_and_review_is_due(client):
    h = await _auth(client, "usage@example.com")
    summary = (await client.get(f"{BASE}/usage", headers=h)).json()
    assert {s["sku"] for s in summary["skus"]} == {
        "geocoding",
        "places_autocomplete",
        "place_details",
        "routes",
        "elevation",
    }
    assert all(s["requests"] == 0 and s["level"] == "ok" for s in summary["skus"])
    budget = summary["budget"]
    assert (budget["currency"], Decimal(budget["budget_amount"]), budget["level"]) == ("INR", Decimal("500"), "ok")
    assert summary["fx_rates"] == {"INR": 83.0}
    assert summary["pricing_review_due"] is True and summary["pricing_last_reviewed_at"] is None

    pricing = (await client.get(f"{BASE}/usage/pricing", headers=h)).json()
    rows = [
        {
            "sku": p["sku"],
            "unit_price_usd_per_1000": p["unit_price_usd_per_1000"],
            "free_monthly_units": p["free_monthly_units"],
        }
        for p in pricing
    ]
    assert (await client.put(f"{BASE}/usage/pricing", json={"rows": rows}, headers=h)).status_code == 200
    reviewed = (await client.get(f"{BASE}/usage", headers=h)).json()
    assert reviewed["pricing_review_due"] is False and reviewed["pricing_last_reviewed_at"]


@pytest.mark.asyncio
async def test_settings_validation_and_currency_choice(client):
    h = await _auth(client, "settings@example.com")
    no_rate = await client.put(f"{BASE}/usage/settings", json={"budget_currency": "EUR"}, headers=h)
    assert no_rate.status_code == 400 and "rate" in no_rate.text
    inverted = await client.put(
        f"{BASE}/usage/settings", json={"budget_amount": "100", "warning_amount": "200"}, headers=h
    )
    assert inverted.status_code == 400
    ok = await client.put(
        f"{BASE}/usage/settings",
        json={
            "budget_currency": "EUR",
            "fx_rates": {"INR": 83.0, "EUR": 0.92},
            "budget_amount": "10",
            "warning_amount": "7",
        },
        headers=h,
    )
    assert ok.status_code == 200 and ok.json()["budget_currency"] == "EUR"
    for bad in (
        {"fx_rates": {"eur": 1}},
        {"fx_rates": {"EUR": -1}},
        {"budget_amount": "-5"},
        {"budget_currency": "EURO"},
    ):
        assert (await client.put(f"{BASE}/usage/settings", json=bad, headers=h)).status_code == 422, bad
    assert (await client.get(f"{BASE}/usage", params={"month": "2027-13"}, headers=h)).status_code == 422


@pytest.mark.asyncio
async def test_summary_counts_requests_blocks_and_converts_spend(client, google):
    h = await _auth(client, "summary@example.com")
    await _connect_google(client, h)
    rows = [{"sku": "geocoding", "unit_price_usd_per_1000": "5000", "free_monthly_units": 1}]
    await client.put(f"{BASE}/usage/pricing", json={"rows": rows}, headers=h)
    # Budget ₹830 = $10. Warning ₹415 = $5.
    await client.put(f"{BASE}/usage/settings", json={"budget_amount": "830", "warning_amount": "415"}, headers=h)
    for _ in range(3):  # 1 free + 2 billed at $5 each
        await client.post(f"{BASE}/maps/reverse-geocode", json={"lat": 1, "lng": 1}, headers=h)

    summary = (await client.get(f"{BASE}/usage", headers=h)).json()
    geo = next(s for s in summary["skus"] if s["sku"] == "geocoding")
    assert geo["requests"] == 3 and geo["free_units"] == 1 and geo["pct_of_free"] == 300.0 and geo["level"] == "limit"
    assert Decimal(geo["estimated_cost_usd"]) == Decimal("10")
    budget = summary["budget"]
    assert Decimal(budget["spent_usd"]) == Decimal("10") and Decimal(budget["spent_in_budget_currency"]) == Decimal(
        "830.00"
    )
    assert budget["level"] == "limit" and budget["non_essential_blocked"] is True

    # Past the budget and past its free allowance, even map taps stop — and are recorded as blocked.
    tap = (await client.post(f"{BASE}/maps/reverse-geocode", json={"lat": 1, "lng": 1}, headers=h)).json()
    assert tap["fallback_reason"] == "cost_protection"
    geo = next(s for s in (await client.get(f"{BASE}/usage", headers=h)).json()["skus"] if s["sku"] == "geocoding")
    assert geo["blocked"] == 1 and geo["requests"] == 3

    # Turning protection off lets requests through again (the user's explicit choice).
    await client.put(f"{BASE}/usage/settings", json={"protection_enabled": False}, headers=h)
    tap = (await client.post(f"{BASE}/maps/reverse-geocode", json={"lat": 1, "lng": 1}, headers=h)).json()
    assert tap["fallback_reason"] is None


@pytest.mark.asyncio
async def test_warning_amount_raises_the_level_early(client, google):
    h = await _auth(client, "warn@example.com")
    await _connect_google(client, h)
    await client.put(
        f"{BASE}/usage/pricing",
        json={"rows": [{"sku": "geocoding", "unit_price_usd_per_1000": "1000", "free_monthly_units": 0}]},
        headers=h,
    )
    # $1 spent of a $10 budget (10%) but past the $0.50 warning amount.
    await client.put(
        f"{BASE}/usage/settings",
        json={"budget_currency": "USD", "budget_amount": "10", "warning_amount": "0.5"},
        headers=h,
    )
    await client.post(f"{BASE}/maps/reverse-geocode", json={"lat": 1, "lng": 1}, headers=h)
    status = (await client.get(f"{BASE}/maps/status", headers=h)).json()
    assert status == {"configured": True, "level": "warning", "non_essential_blocked": False}
