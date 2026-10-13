"""Shared trip plans: property-based tests (PBT-02 round-trips, PBT-03 invariants) for the pure rules."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

from app.core.short_codes import SHORT_CODE_ALPHABET, code_pattern, generate_code, hash_secret, new_secret
from app.modules.travel.export_plan import plan_document_detail
from app.modules.travel.maps_links import parse_maps_url
from app.modules.travel.plan_document import (
    MAX_BACKUPS,
    applied_end_date,
    apply_rows,
    backups_to_prune,
    copy_document,
    day_chains,
    plan_km,
    road_legs,
    summarize,
)
from app.modules.travel.schemas.plan_document import DayRoute, PlanDay, PlanDocument, PlanPlace, PlanStop, RoadLeg
from app.modules.travel.schemas.trips import TripSummary
from app.tests.share_support import lat_lngs, plan_documents, plan_stops
from hypothesis import given, settings
from hypothesis import strategies as st

# ---- round-trips (PBT-02) ----------------------------------------------------------------------


@given(plan_documents())
@settings(deadline=None)
def test_plan_document_json_round_trip(doc):
    assert PlanDocument.model_validate_json(doc.model_dump_json()) == doc
    assert PlanDocument.model_validate(doc.model_dump(mode="json")) == doc  # the stored JSON column shape


# ---- invariants (PBT-03) -----------------------------------------------------------------------


@given(st.integers(min_value=1, max_value=16))
def test_codes_use_only_the_unambiguous_alphabet(length):
    code = generate_code(length)
    assert len(code) == length and set(code) <= set(SHORT_CODE_ALPHABET)
    assert not set("0O1l") & set(code)
    assert re.fullmatch(code_pattern(length), code)


def test_secrets_are_random_and_only_their_hash_is_comparable():
    a, b = new_secret(), new_secret()
    assert a != b and len(a) >= 32
    assert hash_secret(a) == hash_secret(a) and hash_secret(a) != a and len(hash_secret(a)) == 64


@given(plan_documents())
@settings(deadline=None)
def test_a_fresh_copy_compares_as_unchanged(doc):
    summary = summarize(doc, copy_document(doc))
    assert (summary.added, summary.removed, summary.changed) == (0, 0, 0)
    assert summary.stops == len(doc.stops()) and summary.days == len(doc.days)


@given(plan_documents(), st.data())
@settings(deadline=None)
def test_diff_counts_reconcile_with_stop_counts(original, data):
    """Remove some stops, edit some, add new ones: stops(after) == stops(before) - removed + added."""
    edited = copy_document(original)
    for day in edited.days:
        keep = data.draw(st.lists(st.booleans(), min_size=len(day.stops), max_size=len(day.stops)))
        day.stops = [s for s, k in zip(day.stops, keep, strict=True) if k]
    survivors = edited.stops()
    if survivors and data.draw(st.booleans()):
        survivors[0].title = survivors[0].title + " (edited)"
    existing = {s.id for s in original.stops()}
    extra = [s for s in data.draw(st.lists(plan_stops(), max_size=4)) if s.id not in existing]
    extra = list({s.id: s for s in extra}.values())
    edited.days.append(PlanDay(stops=extra))
    edited = PlanDocument.model_validate(edited.model_dump())

    summary = summarize(original, edited)
    assert summary.stops == len(original.stops()) - summary.removed + summary.added
    assert summary.added == len(extra)
    assert 0 <= summary.changed <= len(survivors)


@given(plan_documents(), st.none() | st.dates(min_value=date(2000, 1, 1), max_value=date(2090, 1, 1)))
@settings(deadline=None)
def test_apply_rows_keep_days_stops_order_and_titles(doc, start):
    days = apply_rows(doc, start)
    assert len(days) == len(doc.days)
    for index, (row, day) in enumerate(zip(days, doc.days, strict=True)):
        assert row.day_index == index
        assert row.day_date == (start + timedelta(days=index) if start else None)
        assert [i.title for i in row.items] == [s.title for s in day.stops]
        assert [i.position for i in row.items] == list(range(len(day.stops)))
        assert [i.accommodation for i in row.items] == [s.stay for s in day.stops]


@given(
    st.dates(min_value=date(2000, 1, 1), max_value=date(2090, 1, 1)),
    st.none() | st.dates(min_value=date(2000, 1, 1), max_value=date(2091, 1, 1)),
    st.integers(min_value=0, max_value=120),
)
def test_applied_end_date_spans_exactly_the_plan_days(start, end, days):
    result = applied_end_date(start, end, days)
    if days == 0:
        assert result == end
    else:
        assert (result - start).days + 1 == days
    assert applied_end_date(None, end, days) == end


@given(
    st.lists(
        st.datetimes(min_value=datetime(2026, 1, 1), max_value=datetime(2030, 1, 1)).map(
            lambda d: d.replace(tzinfo=timezone.utc)
        ),
        max_size=12,
        unique=True,
    )
)
def test_backup_pruning_keeps_only_the_newest_five(stamps):
    backups = [(f"b{i}", stamp) for i, stamp in enumerate(stamps)]
    pruned = set(backups_to_prune(backups))
    kept = [b for b in backups if b[0] not in pruned]
    assert len(kept) == min(len(backups), MAX_BACKUPS)
    if pruned:
        assert min(s for _, s in kept) > max(s for i, s in backups if i in pruned)


@given(plan_documents())
@settings(deadline=None)
def test_plan_distance_is_never_negative(doc):
    km = plan_km(doc)
    assert km >= 0
    if sum(1 for s in doc.stops() if s.place is not None) < 2:
        assert km == 0


@given(lat_lngs(), st.sampled_from(["search", "place", "viewport"]))
def test_maps_url_parse_round_trip(point, style):
    """Formatting a point as any common Google Maps link and parsing it back gives the same point."""
    lat, lng = round(point[0], 6), round(point[1], 6)
    la, ln = f"{lat:.6f}", f"{lng:.6f}"  # Google writes fixed-point decimals, never exponents
    url = {
        "search": f"https://www.google.com/maps/search/?api=1&query={la},{ln}",
        "place": f"https://www.google.com/maps/place/Somewhere/@0,0,10z/data=!3d{la}!4d{ln}",
        "viewport": f"https://maps.google.co.in/maps/@{la},{ln},14z",
    }[style]
    parsed = parse_maps_url(url)
    assert parsed is not None
    assert abs(parsed.lat - lat) < 1e-6 and abs(parsed.lng - lng) < 1e-6


# ---- road km per day ----------------------------------------------------------------------------

_TRIP = TripSummary(
    id="t1",
    name="Trip",
    description=None,
    start_date=date(2027, 6, 1),
    end_date=None,
    dates_tentative=False,
    status="planning",
    cover_photo_id=None,
    notes=None,
    confirmed_at=None,
    completed_at=None,
    created_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
    updated_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
)


def _routed(doc: PlanDocument) -> PlanDocument:
    """The plan with a current road route on every day that has legs."""
    routed = doc.model_copy(deep=True)
    for day, chain in zip(routed.days, day_chains(routed), strict=True):
        if len(chain) >= 2:
            day.route = DayRoute(points=chain, legs=[RoadLeg(distance_m=1000.0 * (i + 1)) for i in range(len(chain) - 1)])
    return routed


def _leg_count(doc: PlanDocument) -> int:
    return sum(max(len(chain) - 1, 0) for chain in day_chains(doc))


@given(plan_documents())
@settings(deadline=None)
def test_day_chains_cover_each_leg_of_the_pdf_exactly_once(doc):
    """Day routes line up with the PDF guide's stop sequence, so every road leg lands on its stop."""
    detail, _, roads = plan_document_detail(_TRIP, doc)
    assert _leg_count(doc) == max(len(detail.stops) - 1, 0) == len(roads)
    assert all(road is None for road in roads)  # no route saved: straight-line estimates only


@given(plan_documents())
@settings(deadline=None)
def test_routed_plan_round_trips_and_every_leg_has_road_data(doc):
    routed = _routed(doc)
    assert PlanDocument.model_validate_json(routed.model_dump_json()) == routed
    roads = road_legs(routed)
    assert len(roads) == _leg_count(routed) and all(road is not None for road in roads)


@given(plan_documents(), st.data())
@settings(deadline=None)
def test_a_day_route_counts_only_while_its_chain_is_unchanged(doc, data):
    routed = _routed(doc)
    placed = [stop for stop in routed.stops() if stop.place is not None]
    if not placed:
        return
    before = day_chains(routed)
    moved = data.draw(st.sampled_from(placed))
    moved.place = moved.place.model_copy(update={"lat": moved.place.lat + (0.5 if moved.place.lat < 0 else -0.5)})
    after = day_chains(routed)
    expected = [
        known
        for old, new in zip(before, after, strict=True)
        for known in [old == new] * max(len(new) - 1, 0)
    ]
    assert [road is not None for road in road_legs(routed)] == expected


def test_back_to_back_stops_at_one_place_are_one_point_and_days_start_where_the_last_ended():
    def stop(sid: str, lat: float | None) -> PlanStop:
        place = PlanPlace(name=f"P{lat}", lat=lat, lng=77.0) if lat is not None else None
        return PlanStop(id=sid, title=sid, place=place)

    doc = PlanDocument(
        days=[
            PlanDay(stops=[stop("a", 32.0), stop("b", 32.0), stop("note", None), stop("c", 32.5)]),
            PlanDay(stops=[]),
            PlanDay(stops=[stop("d", 32.5), stop("e", 33.0)]),
        ]
    )
    assert day_chains(doc) == [[(32.0, 77.0), (32.5, 77.0)], [], [(32.5, 77.0), (33.0, 77.0)]]
