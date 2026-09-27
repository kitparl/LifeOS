"""Travel OS U1 — geo math, usage tracking / cost protection rules, places, and the maps proxy.

Pure rules are property-tested with Hypothesis; everything crossing the trust boundary (ownership,
input bounds, the Google key) goes through the API. Google is always faked: `FakeGoogle` routes by
host/path and records every request so tests can assert "exactly one usage event per upstream call".
"""

from __future__ import annotations

import math
from decimal import Decimal

import pytest
from app.modules.travel.geo import (
    bbox_for_radius,
    decode_polyline,
    elevation_gain_loss,
    encode_polyline,
    haversine_m,
    simplify_dp,
    within_radius,
)
from app.modules.travel.models import MapsUsageEvent
from app.modules.travel.services.usage_service import (
    block_reason,
    build_sku_usage,
    marginal_cost_usd,
    usage_level,
)
from app.tests.travel_support import auth as _auth
from app.tests.travel_support import connect_google as _connect_google
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import select

BASE = "/api/v1/travel"

lats = st.floats(min_value=-90, max_value=90, allow_nan=False)
lngs = st.floats(min_value=-180, max_value=180, allow_nan=False)
points = st.tuples(lats, lngs)
# Realistic track coordinates (avoid the poles, where 1e-5 degrees of longitude is sub-millimetre).
track_points = st.tuples(
    st.floats(min_value=-85, max_value=85, allow_nan=False),
    st.floats(min_value=-179.9, max_value=179.9, allow_nan=False),
)


# ---- geo properties ----------------------------------------------------------------------------


@given(a=points, b=points)
@settings(deadline=None)
def test_haversine_symmetric_non_negative_bounded(a, b):
    d = haversine_m(a, b)
    assert d >= 0
    assert math.isclose(d, haversine_m(b, a), rel_tol=1e-9, abs_tol=1e-6)
    assert d <= math.pi * 6_371_008.8 + 1
    assert haversine_m(a, a) == pytest.approx(0, abs=1e-6)


@given(center=points, other=points, radius_m=st.floats(min_value=1, max_value=5_000_000))
@settings(deadline=None, max_examples=300)
def test_bbox_prefilter_never_drops_a_true_match(center, other, radius_m):
    if within_radius(center, other, radius_m):
        assert bbox_for_radius(center, radius_m).contains(*other)


@given(pts=st.lists(track_points, max_size=40))
@settings(deadline=None)
def test_polyline_round_trip(pts):
    decoded = decode_polyline(encode_polyline(pts))
    assert len(decoded) == len(pts)
    for (lat, lng), (dlat, dlng) in zip(pts, decoded, strict=True):
        assert dlat == pytest.approx(round(lat, 5), abs=1e-9)
        assert dlng == pytest.approx(round(lng, 5), abs=1e-9)


def test_polyline_known_value():
    # Google's documented example.
    pts = [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]
    assert encode_polyline(pts) == "_p~iF~ps|U_ulLnnqC_mqNvxq`@"


@given(pts=st.lists(track_points, max_size=60), tol=st.floats(min_value=0, max_value=5000))
@settings(deadline=None)
def test_simplify_keeps_endpoints_and_is_a_subsequence(pts, tol):
    out = simplify_dp(pts, tol)
    assert len(out) <= len(pts)
    if pts:
        assert out[0] == pts[0] and out[-1] == pts[-1]
    it = iter(pts)
    assert all(any(p == q for q in it) for p in out)


@given(elev=st.lists(st.floats(min_value=-500, max_value=9000, allow_nan=False), min_size=1, max_size=80))
@settings(deadline=None)
def test_elevation_gain_loss_invariants(elev):
    gain, loss = elevation_gain_loss(elev)
    assert gain >= 0 and loss >= 0
    assert gain - loss == pytest.approx(elev[-1] - elev[0], abs=1e-6)


# ---- usage / protection properties -------------------------------------------------------------


@given(
    prior=st.integers(min_value=0, max_value=100_000),
    units=st.integers(min_value=0, max_value=1_000),
    free=st.integers(min_value=0, max_value=50_000),
    price=st.decimals(min_value=0, max_value=100, places=2),
)
def test_marginal_cost_is_non_negative_and_additive(prior, units, free, price):
    one = marginal_cost_usd(prior, units, free, price)
    assert one >= 0
    split = marginal_cost_usd(prior, units // 2, free, price) + marginal_cost_usd(
        prior + units // 2, units - units // 2, free, price
    )
    assert abs(one - split) <= Decimal("0.000002")
    if prior + units <= free:
        assert one == 0


@given(
    rows=st.lists(
        st.tuples(
            st.sampled_from(["geocoding", "routes", "unknown"]),
            st.sampled_from(["ok", "error", "blocked"]),
            st.integers(min_value=0, max_value=500),
            st.decimals(min_value=0, max_value=50, places=6),
        ),
        max_size=30,
    )
)
def test_summary_total_matches_events_for_priced_skus(rows):
    class Price:
        def __init__(self, sku):
            self.sku, self.label, self.free_monthly_units = sku, sku, 100

    skus = build_sku_usage(rows, [Price("geocoding"), Price("routes")])
    total = sum((s.estimated_cost_usd for s in skus), Decimal(0))
    assert total == sum((c for sku, _, _, c in rows if sku in ("geocoding", "routes")), Decimal(0))
    assert all(s.requests >= 0 and s.blocked >= 0 for s in skus)


def test_usage_levels_follow_spec_thresholds():
    assert [usage_level(p) for p in (None, 10, 50, 70, 85, 95, 100, 150)] == [
        "ok",
        "ok",
        "info",
        "warning",
        "high",
        "critical",
        "limit",
        "limit",
    ]


def _reason(**overrides):
    args = dict(
        protection_enabled=True,
        stop_at_free_tier=False,
        spent_usd=Decimal(0),
        budget_usd=Decimal(5),
        sku_units=0,
        free_units=10,
        essential=False,
    )
    args.update(overrides)
    return block_reason(**args)


def test_block_reason_rules():
    assert _reason() is None
    assert _reason(protection_enabled=False, spent_usd=Decimal(99)) is None
    assert _reason(spent_usd=Decimal(5)) == "budget_reached"
    # Essential (map tap) keeps working past the budget only while its own free allowance lasts.
    assert _reason(spent_usd=Decimal(5), essential=True, sku_units=9) is None
    assert _reason(spent_usd=Decimal(5), essential=True, sku_units=10) == "budget_reached"
    assert _reason(stop_at_free_tier=True, sku_units=10) == "free_allowance_used"
    assert _reason(budget_usd=None, spent_usd=Decimal(1000)) is None


# ---- helpers ------------------------------------------------------------------------------------


async def _events(client) -> list[MapsUsageEvent]:
    async with client.session_factory() as session:
        return list((await session.execute(select(MapsUsageEvent))).scalars().all())


def _place(**overrides) -> dict:
    body = {"name": "Hampta Pass", "lat": 32.2667, "lng": 77.3667, "category": "trek"}
    body.update(overrides)
    return body


# ---- places API --------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_map_tap_without_key_falls_back_and_saving_still_works(client):
    h = await _auth(client, "tap@example.com")
    geo = await client.post(f"{BASE}/maps/reverse-geocode", json={"lat": 32.2667, "lng": 77.3667}, headers=h)
    assert geo.status_code == 200
    assert geo.json() == {"result": None, "fallback_reason": "missing_credential"}
    assert await _events(client) == []  # nothing was sent, so nothing is recorded

    created = await client.post(f"{BASE}/places", json=_place(), headers=h)
    assert created.status_code == 201, created.text
    place = created.json()
    assert place["status"] == "wishlist" and place["external_source"] is None

    markers = (await client.get(f"{BASE}/markers", headers=h)).json()
    assert markers == [
        {
            "id": place["id"],
            "kind": "place",
            "lat": 32.2667,
            "lng": 77.3667,
            "label": "Hampta Pass",
            "status": "wishlist",
            "trip_id": None,
        }
    ]


@pytest.mark.asyncio
async def test_same_spot_or_same_google_place_is_not_duplicated(client):
    h = await _auth(client, "dup@example.com")
    first = (await client.post(f"{BASE}/places", json=_place(external_place_id="ChIJx"), headers=h)).json()
    again = await client.post(f"{BASE}/places", json=_place(lat=32.266701), headers=h)
    assert again.status_code == 409
    assert again.json()["detail"]["place_id"] == first["id"]
    other_spot_same_id = await client.post(
        f"{BASE}/places", json=_place(lat=10, lng=10, external_place_id="ChIJx"), headers=h
    )
    assert other_spot_same_id.status_code == 409


@pytest.mark.asyncio
async def test_place_crud_filters_tags_and_near(client):
    h = await _auth(client, "crud@example.com")
    manali = (
        await client.post(
            f"{BASE}/places",
            json=_place(name="Manali", lat=32.2432, lng=77.1892, category="city", tags=["Himachal", "hills"]),
            headers=h,
        )
    ).json()
    await client.post(f"{BASE}/places", json=_place(), headers=h)
    await client.post(f"{BASE}/places", json=_place(name="Goa", lat=15.3, lng=74.1, category="beach"), headers=h)

    assert manali["tags"] == ["hills", "Himachal"]
    listed = await client.get(f"{BASE}/places", params={"category": "city"}, headers=h)
    assert [p["name"] for p in listed.json()] == ["Manali"] and listed.headers["X-Total-Count"] == "1"
    by_tag = await client.get(f"{BASE}/places", params={"tag": "himachal"}, headers=h)
    assert [p["name"] for p in by_tag.json()] == ["Manali"]

    near = (
        await client.get(f"{BASE}/places/near", params={"lat": 32.24, "lng": 77.19, "radius_km": 100}, headers=h)
    ).json()
    assert [p["name"] for p in near] == ["Manali", "Hampta Pass"]
    assert near[0]["distance_m"] < near[1]["distance_m"]

    patched = await client.patch(
        f"{BASE}/places/{manali['id']}", json={"status": "visited", "notes": "Old town"}, headers=h
    )
    assert patched.json()["status"] == "visited"
    assert (await client.get(f"{BASE}/tags", headers=h)).json() == ["hills", "Himachal"]
    assert (await client.delete(f"{BASE}/places/{manali['id']}", headers=h)).status_code == 204
    assert (await client.get(f"{BASE}/places/{manali['id']}", headers=h)).status_code == 404


@pytest.mark.asyncio
async def test_places_are_private_to_their_owner(client):
    owner = await _auth(client, "owner@example.com")
    intruder = await _auth(client, "intruder@example.com")
    place = (await client.post(f"{BASE}/places", json=_place(), headers=owner)).json()
    for method, url, body in (
        ("get", f"{BASE}/places/{place['id']}", None),
        ("patch", f"{BASE}/places/{place['id']}", {"name": "Mine"}),
        ("delete", f"{BASE}/places/{place['id']}", None),
        ("get", f"{BASE}/places/{place['id']}/history", None),
    ):
        resp = await client.request(method, url, json=body, headers=intruder)
        assert resp.status_code == 404, (method, url)
    assert (await client.get(f"{BASE}/places", headers=intruder)).json() == []
    assert (await client.get(f"{BASE}/places")).status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        _place(lat=91),
        _place(lng=-181),
        _place(name="   "),
        _place(name="x" * 201),
        _place(links=["javascript:alert(1)"]),
        _place(status="bogus"),
        _place(tags=["t"] * 21),
    ],
)
async def test_place_input_is_bounded(client, body):
    h = await _auth(client, "bounds@example.com")
    assert (await client.post(f"{BASE}/places", json=body, headers=h)).status_code == 422


# ---- maps proxy with a Google key ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_key_is_masked_and_never_returned(client, google):
    h = await _auth(client, "key@example.com")
    await _connect_google(client, h)
    status = (await client.get("/api/v1/integrations/google-maps", headers=h)).json()
    assert status["configured"] is True and status["api_key_masked"] == "****1234"
    assert "AIzaTESTKEY1234" not in str(status)
    providers = (await client.get("/api/v1/integrations/providers", headers=h)).json()
    assert any(p["provider"] == "google_maps" for p in providers)


@pytest.mark.asyncio
async def test_reverse_geocode_goes_through_tracker_once(client, google):
    h = await _auth(client, "geo@example.com")
    await _connect_google(client, h)
    resp = await client.post(f"{BASE}/maps/reverse-geocode", json={"lat": 32.2667, "lng": 77.3667}, headers=h)
    body = resp.json()
    assert body["fallback_reason"] is None
    assert body["result"]["name"] == "Hampta Pass"
    assert body["result"]["region"] == "Himachal Pradesh"
    assert body["result"]["lat"] == 32.2667  # the tapped point, not the geocoder's
    assert len(google.requests) == 1
    events = await _events(client)
    assert [(e.sku, e.feature, e.outcome) for e in events] == [("geocoding", "map_tap", "ok")]
    assert events[0].estimated_cost_usd == 0  # inside the free allowance


@pytest.mark.asyncio
async def test_search_then_select_uses_session_and_is_tracked(client, google):
    h = await _auth(client, "search@example.com")
    await _connect_google(client, h)
    session = "sess-1234abcd"
    sugg = (await client.get(f"{BASE}/maps/autocomplete", params={"q": "Mana", "session": session}, headers=h)).json()
    assert sugg["suggestions"][0]["primary"] == "Manali"
    detail = (await client.get(f"{BASE}/maps/place/ChIJmanali", params={"session": session}, headers=h)).json()
    assert detail["result"]["external_place_id"] == "ChIJmanali"
    auto_req, detail_req = google.requests
    assert auto_req.headers["X-Goog-Api-Key"] == "AIzaTESTKEY1234"
    assert detail_req.url.params["sessionToken"] == session
    assert "addressComponents" in detail_req.headers["X-Goog-FieldMask"]
    assert [e.sku for e in await _events(client)] == ["places_autocomplete", "place_details"]
    too_short = await client.get(f"{BASE}/maps/autocomplete", params={"q": "Ma", "session": session}, headers=h)
    assert too_short.status_code == 400


@pytest.mark.asyncio
async def test_google_error_is_recorded_and_falls_back(client, google):
    h = await _auth(client, "err@example.com")
    await _connect_google(client, h)
    google.status = 403
    resp = (await client.post(f"{BASE}/maps/reverse-geocode", json={"lat": 1, "lng": 1}, headers=h)).json()
    assert resp == {"result": None, "fallback_reason": "invalid_credential"}
    assert [(e.outcome, e.estimated_cost_usd) for e in await _events(client)] == [("error", 0)]


@pytest.mark.asyncio
async def test_cost_protection_blocks_before_reaching_google(client, google):
    h = await _auth(client, "budget@example.com")
    await _connect_google(client, h)
    # No free allowance and a tiny budget: the first paid search spends it.
    pricing = await client.put(
        f"{BASE}/usage/pricing",
        json={"rows": [{"sku": "places_autocomplete", "unit_price_usd_per_1000": "5000", "free_monthly_units": 0}]},
        headers=h,
    )
    assert pricing.status_code == 200, pricing.text
    await client.put(
        f"{BASE}/usage/settings",
        json={"budget_amount": "1", "warning_amount": "0.5", "budget_currency": "USD"},
        headers=h,
    )
    q = {"q": "Manali", "session": "sess-1234abcd"}
    first = (await client.get(f"{BASE}/maps/autocomplete", params=q, headers=h)).json()
    assert first["fallback_reason"] is None
    second = (await client.get(f"{BASE}/maps/autocomplete", params=q, headers=h)).json()
    assert second == {"suggestions": [], "fallback_reason": "cost_protection"}
    assert len(google.requests) == 1  # the blocked call never left the server
    # Map taps are essential: still allowed while geocoding's own free allowance lasts.
    tap = (await client.post(f"{BASE}/maps/reverse-geocode", json={"lat": 1, "lng": 1}, headers=h)).json()
    assert tap["fallback_reason"] is None
    events = [(e.sku, e.outcome) for e in await _events(client)]
    assert events == [("places_autocomplete", "ok"), ("places_autocomplete", "blocked"), ("geocoding", "ok")]
    status = (await client.get(f"{BASE}/maps/status", headers=h)).json()
    assert status == {"configured": True, "level": "limit", "non_essential_blocked": True}


@pytest.mark.asyncio
async def test_connection_test_is_tracked(client, google):
    h = await _auth(client, "test@example.com")
    await _connect_google(client, h)
    resp = (await client.post("/api/v1/integrations/google-maps/test", headers=h)).json()
    assert resp["ok"] is True
    assert [(e.feature, e.outcome) for e in await _events(client)] == [("connection_test", "ok")]


@pytest.mark.asyncio
async def test_maps_proxy_is_rate_limited_per_user(client, google):
    h = await _auth(client, "spam@example.com")
    await _connect_google(client, h)
    codes = [
        (await client.post(f"{BASE}/maps/reverse-geocode", json={"lat": 1, "lng": 1}, headers=h)).status_code
        for _ in range(61)
    ]
    assert codes[:60] == [200] * 60 and codes[60] == 429
