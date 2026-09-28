"""Travel OS U2 — trips, drafts, itinerary ordering, map/route sync and calendar mirroring."""

from __future__ import annotations

import pytest
from app.modules.calendar.models import CalendarEvent
from app.modules.travel.itinerary import InvalidOrder, ItemRef, apply_order, stop_sequence, stops_fingerprint
from app.modules.travel.lifecycle import can_transition, promoted_status, reverted_status, visited_status
from app.modules.travel.models import MapsUsageEvent
from app.tests.travel_support import auth as _auth
from app.tests.travel_support import connect_google as _connect_google
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import select

BASE = "/api/v1/travel"
PLACE_STATUSES = ["wishlist", "planned", "visited", "favourite"]


# ---- pure rules ----------------------------------------------------------------------------------


@st.composite
def layouts(draw):
    """Days with items, plus a random target layout that moves items between days."""
    day_ids = [f"d{i}" for i in range(draw(st.integers(min_value=1, max_value=6)))]
    item_ids = [f"i{i}" for i in range(draw(st.integers(min_value=0, max_value=25)))]
    items = [
        ItemRef(id=i, day_id=draw(st.sampled_from(day_ids)), position=n, place_id=None) for n, i in enumerate(item_ids)
    ]
    target_days = draw(st.lists(st.sampled_from(day_ids), unique=True, min_size=1))
    target: dict[str, list[str]] = {d: [] for d in target_days}
    for item_id in draw(st.permutations(item_ids)):
        target[draw(st.sampled_from(sorted(target)))].append(item_id)
    return day_ids, items, target


@given(layouts())
@settings(deadline=None)
def test_reorder_keeps_every_item_once_with_contiguous_positions(case):
    day_ids, items, target = case
    layout = apply_order(day_ids, items, target)
    assert sorted(layout) == sorted(i.id for i in items)
    per_day: dict[str, list[int]] = {}
    for day_id, position in layout.values():
        per_day.setdefault(day_id, []).append(position)
    for positions in per_day.values():
        assert sorted(positions) == list(range(len(positions)))


@given(layouts(), st.data())
@settings(deadline=None)
def test_reorder_rejects_lost_or_duplicated_items(case, data):
    day_ids, items, target = case
    if not items:
        return
    day = data.draw(st.sampled_from(sorted(target)))
    broken = {d: list(ids) for d, ids in target.items()}
    if broken[day] and data.draw(st.booleans()):
        broken[day].pop()
    else:
        broken[day].append(items[0].id)
    with pytest.raises(InvalidOrder):
        apply_order(day_ids, items, broken)


def test_reorder_rejects_foreign_days():
    with pytest.raises(InvalidOrder):
        apply_order(["d1"], [ItemRef("a", "d1", 0, None)], {"other-trip-day": ["a"]})


@given(st.sampled_from(PLACE_STATUSES))
def test_confirm_then_revert_restores_the_place(status):
    promoted = promoted_status(status)
    after_confirm = promoted or status
    back = reverted_status(after_confirm, promoted_by_trip=promoted is not None) or after_confirm
    assert back == status
    assert visited_status("favourite") is None and visited_status("visited") is None


def test_lifecycle_table():
    assert can_transition("draft", "planning")
    assert not can_transition("draft", "completed")
    assert can_transition("booked", "draft")
    assert not can_transition("completed", "draft")


def test_stop_sequence_orders_by_day_then_position_and_collapses_repeats():
    items = [
        ItemRef("x", "d2", 0, "chandratal"),
        ItemRef("a", "d1", 1, "hampta"),
        ItemRef("b", "d1", 0, "manali"),
        ItemRef("c", "d1", 2, "hampta"),
        ItemRef("d", "d1", 3, None),
    ]
    places = {
        "manali": ("Manali", 32.2, 77.1),
        "hampta": ("Hampta", 32.3, 77.3),
        "chandratal": ("Chandratal", 32.5, 77.6),
    }
    stops = stop_sequence(["d1", "d2"], items, places)
    assert [s.place_id for s in stops] == ["manali", "hampta", "chandratal"]
    assert [s.day_id for s in stops] == ["d1", "d1", "d2"]
    assert stops_fingerprint(stops, "driving") != stops_fingerprint(stops[::-1], "driving")
    assert stops_fingerprint(stops, "driving") != stops_fingerprint(stops, "walking")


# ---- API -----------------------------------------------------------------------------------------


async def _place(client, h, name, lat, lng) -> str:
    resp = await client.post(f"{BASE}/places", json={"name": name, "lat": lat, "lng": lng}, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _rows(client, model):
    async with client.session_factory() as session:
        return list((await session.execute(select(model))).scalars().all())


async def _himachal(client, h):
    places = {
        "manali": await _place(client, h, "Manali", 32.2432, 77.1892),
        "hampta": await _place(client, h, "Hampta Pass", 32.2667, 77.3667),
        "chandratal": await _place(client, h, "Chandratal", 32.4753, 77.6178),
    }
    trip = (await client.post(f"{BASE}/trips", json={"name": "Himachal 2027"}, headers=h)).json()
    return places, trip["trip"]["id"]


async def _dated_itinerary(client, h, places, tid, start="2027-06-12", end="2027-06-21"):
    await client.patch(f"{BASE}/trips/{tid}", json={"start_date": start, "end_date": end}, headers=h)
    detail = (await client.post(f"{BASE}/trips/{tid}/days/fill", headers=h)).json()
    d1, d2 = detail["days"][0]["id"], detail["days"][1]["id"]
    for name, day in (("manali", d1), ("hampta", d1), ("chandratal", d2)):
        detail = (
            await client.post(f"{BASE}/trips/{tid}/places/{places[name]}", json={"day_id": day}, headers=h)
        ).json()
    return detail, d1, d2


@pytest.mark.asyncio
async def test_draft_trip_can_be_saved_half_done(client):
    h = await _auth(client, "draft@example.com")
    places, tid = await _himachal(client, h)
    trip = (await client.get(f"{BASE}/trips/{tid}", headers=h)).json()
    assert trip["trip"]["status"] == "draft" and trip["trip"]["start_date"] is None

    assert (await client.post(f"{BASE}/trips/{tid}/days/fill", headers=h)).status_code == 400
    day = (await client.post(f"{BASE}/trips/{tid}/days", json={"title": "Somewhere"}, headers=h)).json()
    assert day["days"][0]["day_date"] is None  # undated draft day

    for pid in places.values():
        detail = (await client.post(f"{BASE}/trips/{tid}/places/{pid}", headers=h)).json()
    assert {p["status"] for p in detail["places"]} == {"wishlist"}  # drafts do not plan places
    cannot = await client.post(f"{BASE}/trips/{tid}/confirm", headers=h)
    assert cannot.status_code == 400 and "dates" in cannot.text
    assert await _rows(client, CalendarEvent) == []


@pytest.mark.asyncio
async def test_itinerary_map_route_and_lifecycle(client):
    h = await _auth(client, "journey@example.com")
    places, tid = await _himachal(client, h)
    detail, d1, d2 = await _dated_itinerary(client, h, places, tid)
    assert len(detail["days"]) == 10
    assert detail["days"][4]["day_date"] == "2027-06-16"
    assert [s["name"] for s in detail["stops"]] == ["Manali", "Hampta Pass", "Chandratal"]

    # Route without a Google key: straight line, clearly labelled, nothing tracked.
    route = (await client.post(f"{BASE}/trips/{tid}/route", json={"mode": "driving"}, headers=h)).json()
    assert route["source"] == "straight_line" and route["fallback_reason"] == "missing_credential"
    assert route["legs"] is None
    assert route["distance_m"] > 40_000 and route["duration_s"] is None
    assert (await client.get(f"{BASE}/trips/{tid}", headers=h)).json()["route"]["is_stale"] is False
    assert await _rows(client, MapsUsageEvent) == []

    # Reorder: Chandratal moves before Hampta on day 1 — one request, the map follows, the route goes stale.
    items = {i["title"]: i["id"] for d in detail["days"] for i in d["items"]}
    order = {d1: [items["Manali"], items["Chandratal"], items["Hampta Pass"]], d2: []}
    detail = (await client.put(f"{BASE}/trips/{tid}/itinerary/order", json={"days": order}, headers=h)).json()
    assert [s["name"] for s in detail["stops"]] == ["Manali", "Chandratal", "Hampta Pass"]
    assert detail["route"]["is_stale"] is True
    lost = await client.put(f"{BASE}/trips/{tid}/itinerary/order", json={"days": {d1: [items["Manali"]]}}, headers=h)
    assert lost.status_code == 400

    # Changing dates re-dates the itinerary.
    detail = (
        await client.patch(
            f"{BASE}/trips/{tid}", json={"start_date": "2027-06-13", "end_date": "2027-06-22"}, headers=h
        )
    ).json()
    assert detail["days"][0]["day_date"] == "2027-06-13"

    # Confirm: places planned, calendar mirrored.
    detail = (await client.post(f"{BASE}/trips/{tid}/confirm", headers=h)).json()
    assert detail["trip"]["status"] == "planning"
    assert {p["status"] for p in detail["places"]} == {"planned"}
    events = await _rows(client, CalendarEvent)
    assert [(e.source_module, e.source_id, e.all_day) for e in events] == [("travel", tid, True)]
    assert events[0].starts_at.date().isoformat() == "2027-06-13"

    # Back to draft undoes only this trip's promotion and removes the calendar event.
    detail = (await client.post(f"{BASE}/trips/{tid}/draft", headers=h)).json()
    assert {p["status"] for p in detail["places"]} == {"wishlist"}
    assert await _rows(client, CalendarEvent) == []

    await client.post(f"{BASE}/trips/{tid}/confirm", headers=h)
    assert (await client.post(f"{BASE}/trips/{tid}/status", json={"status": "booked"}, headers=h)).status_code == 200
    detail = (await client.post(f"{BASE}/trips/{tid}/complete", headers=h)).json()
    assert detail["trip"]["status"] == "completed"
    assert {p["status"] for p in detail["places"]} == {"visited"}
    # Planning data is kept (spec §21).
    assert len(detail["days"]) == 10 and detail["route"] is not None
    history = (await client.get(f"{BASE}/places/{places['hampta']}/history", headers=h)).json()
    assert [t["name"] for t in history["trips"]] == ["Himachal 2027"]
    assert history["route_ids"] == [detail["route"]["id"]]


@pytest.mark.asyncio
async def test_favourite_is_never_downgraded_and_deleting_trip_keeps_places(client):
    h = await _auth(client, "fav@example.com")
    pid = await _place(client, h, "Spiti", 32.2, 78.0)
    await client.patch(f"{BASE}/places/{pid}", json={"status": "favourite"}, headers=h)
    body = {"name": "Spiti", "start_date": "2027-07-01", "end_date": "2027-07-03"}
    tid = (await client.post(f"{BASE}/trips", json=body, headers=h)).json()["trip"]["id"]
    await client.post(f"{BASE}/trips/{tid}/places/{pid}", headers=h)
    await client.post(f"{BASE}/trips/{tid}/confirm", headers=h)
    await client.post(f"{BASE}/trips/{tid}/complete", headers=h)
    assert (await client.get(f"{BASE}/places/{pid}", headers=h)).json()["status"] == "favourite"
    assert (await client.delete(f"{BASE}/places/{pid}", headers=h)).status_code == 409  # still in a trip
    assert (await client.delete(f"{BASE}/trips/{tid}", headers=h)).status_code == 204
    assert (await client.get(f"{BASE}/places/{pid}", headers=h)).status_code == 200
    assert await _rows(client, CalendarEvent) == []


@pytest.mark.asyncio
async def test_trips_are_private_and_linked_ids_are_checked(client):
    owner = await _auth(client, "tripowner@example.com")
    other = await _auth(client, "tripother@example.com")
    my_place = await _place(client, owner, "Mine", 10, 10)
    my_trip = (await client.post(f"{BASE}/trips", json={"name": "Mine"}, headers=owner)).json()["trip"]["id"]
    their_trip = (await client.post(f"{BASE}/trips", json={"name": "Theirs"}, headers=other)).json()["trip"]["id"]

    assert (await client.get(f"{BASE}/trips/{my_trip}", headers=other)).status_code == 404
    assert (await client.post(f"{BASE}/trips/{my_trip}/confirm", headers=other)).status_code == 404
    # Cannot pull someone else's place into your own trip (IDOR).
    assert (await client.post(f"{BASE}/trips/{their_trip}/places/{my_place}", headers=other)).status_code == 400
    assert [t["name"] for t in (await client.get(f"{BASE}/trips", headers=other)).json()] == ["Theirs"]


@pytest.mark.asyncio
async def test_trip_input_is_bounded(client):
    h = await _auth(client, "tripbounds@example.com")
    too_long = {"name": "x", "start_date": "2027-01-01", "end_date": "2027-12-31"}
    assert (await client.post(f"{BASE}/trips", json=too_long, headers=h)).status_code == 422
    backwards = {"name": "x", "start_date": "2027-01-05", "end_date": "2027-01-01"}
    assert (await client.post(f"{BASE}/trips", json=backwards, headers=h)).status_code == 422


@pytest.mark.asyncio
async def test_google_route_is_tracked(client, google):
    h = await _auth(client, "groute@example.com")
    await _connect_google(client, h)
    places, tid = await _himachal(client, h)
    await _dated_itinerary(client, h, places, tid)
    route = (await client.post(f"{BASE}/trips/{tid}/route", json={"mode": "driving"}, headers=h)).json()
    assert route["source"] == "google" and route["distance_m"] == 123456 and route["duration_s"] == 7200
    assert [(leg["distance_m"], leg["duration_s"]) for leg in route["legs"]] == [(50000, 3000), (73456, 4200)]
    detail = (await client.get(f"{BASE}/trips/{tid}", headers=h)).json()
    assert len(detail["route"]["legs"]) == len(detail["stops"]) - 1
    assert all(s["day_id"] for s in detail["stops"])
    (body,) = google.bodies("directions/v2:computeRoutes")
    assert body["travelMode"] == "DRIVE" and len(body["intermediates"]) == 1
    events = [(e.sku, e.feature, e.outcome) for e in await _rows(client, MapsUsageEvent)]
    assert events == [("routes", "trip_route", "ok")]


@pytest.mark.asyncio
async def test_drawn_route_round_trip(client):
    h = await _auth(client, "draw@example.com")
    body = {
        "name": "My ridge",
        "points": [[32.1, 77.1], [32.2, 77.2], [32.25, 77.3]],
        "waypoints": [{"lat": 32.2, "lng": 77.2, "name": "Camp"}],
    }
    route = (await client.post(f"{BASE}/routes", json=body, headers=h)).json()
    assert route["source"] == "user_drawn"
    assert route["points"] == [[32.1, 77.1], [32.2, 77.2], [32.25, 77.3]]
    assert route["distance_m"] > 20_000
    assert (await client.post(f"{BASE}/routes", json={**body, "points": [[1, 1]]}, headers=h)).status_code == 422
