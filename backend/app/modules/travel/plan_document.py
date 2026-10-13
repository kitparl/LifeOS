"""Shared trip plans, the pure part: trip <-> plan document, comparison with the Original, apply rows.

No DB, no I/O (same split as `itinerary.py` / `export_plan.py`), so every rule here is covered by
property tests.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from itertools import pairwise

from app.modules.travel.geo import Point, decode_polyline, encode_polyline, haversine_m, simplify_dp
from app.modules.travel.models import TravelPlace
from app.modules.travel.schemas.plan_document import DayRoute, PlanDay, PlanDocument, PlanPlace, PlanStop, RoadLeg
from app.modules.travel.schemas.routes import RouteOut
from app.modules.travel.schemas.shares import PlanSummary
from app.modules.travel.schemas.trips import DayOut

MAX_BACKUPS = 5
# Road paths are kept for the PDF's day maps only; ~30 m of detail is plenty and keeps plans small.
ROUTE_TOLERANCE_M = 30
_SAME_POINT_DEG = 1e-7


def new_stop_id() -> str:
    return str(uuid.uuid4())


def snapshot_from_trip(
    days: Sequence[DayOut], places: Mapping[str, TravelPlace], route: RouteOut | None = None
) -> PlanDocument:
    """The trip's days and stops as a plan. Only itinerary fields; trip notes, photos etc. never enter.

    A current trip `route` is kept, split per day, so friends see road km without a new Google call.
    """
    plan_days = []
    for day in sorted(days, key=lambda d: d.day_index):
        stops = []
        for item in sorted(day.items, key=lambda i: i.position):
            place = places.get(item.place_id) if item.place_id else None
            stops.append(
                PlanStop(
                    id=new_stop_id(),
                    title=item.title,
                    place=(
                        PlanPlace(
                            name=place.name, lat=place.lat, lng=place.lng, google_place_id=place.external_place_id
                        )
                        if place is not None
                        else None
                    ),
                    start_time=item.start_time,
                    end_time=item.end_time,
                    transport=item.transport,
                    stay=item.accommodation,
                    notes=item.notes,
                    links=list(item.links or []),
                )
            )
        plan_days.append(PlanDay(title=day.title, notes=day.notes, stops=stops))
    doc = PlanDocument(days=plan_days)
    if route is not None and not route.is_stale and route.legs:
        legs = [RoadLeg(distance_m=leg.distance_m, duration_s=leg.duration_s, polyline=leg.polyline) for leg in route.legs]
        _attach_trip_route(doc, route.mode, legs)
    return doc


def _attach_trip_route(doc: PlanDocument, mode: str, legs: list[RoadLeg]) -> None:
    chains = day_chains(doc)
    if sum(max(len(chain) - 1, 0) for chain in chains) != len(legs):
        return  # the route was computed for other stops
    start = 0
    for day, chain in zip(doc.days, chains, strict=True):
        count = max(len(chain) - 1, 0)
        if count:
            day.route = DayRoute(
                mode=mode, points=chain, legs=[slim_leg(leg) for leg in legs[start : start + count]]
            )
        start += count


def slim_leg(leg: RoadLeg) -> RoadLeg:
    """The leg with its road path simplified (see `ROUTE_TOLERANCE_M`)."""
    if not leg.polyline:
        return leg
    path = encode_polyline(simplify_dp(decode_polyline(leg.polyline), ROUTE_TOLERANCE_M))
    return leg.model_copy(update={"polyline": path})


def day_chains(doc: PlanDocument) -> list[list[Point]]:
    """Per day, the points its legs run through: where the trip was before the day (the last place
    so far) and then each new place of the day. Back-to-back stops at the same place are one point,
    as in `itinerary.stop_sequence`. A day without legs has an empty chain."""
    chains: list[list[Point]] = []
    last: tuple[tuple, Point] | None = None
    for day in doc.days:
        chain: list[Point] = []
        for stop in day.stops:
            if stop.place is None:
                continue
            key = (stop.place.google_place_id or "", stop.place.lat, stop.place.lng)
            point = (stop.place.lat, stop.place.lng)
            if last is not None and key != last[0]:
                chain.extend([last[1], point] if not chain else [point])
            last = (key, point)
        chains.append(chain)
    return chains


def _same_points(a: Sequence[Point], b: Sequence[Point]) -> bool:
    return len(a) == len(b) and all(
        abs(p[0] - q[0]) <= _SAME_POINT_DEG and abs(p[1] - q[1]) <= _SAME_POINT_DEG for p, q in zip(a, b, strict=True)
    )


def road_legs(doc: PlanDocument) -> list[RoadLeg | None]:
    """One entry per leg of the whole plan, in order: the road leg where the day's route is current, else None."""
    legs: list[RoadLeg | None] = []
    for day, chain in zip(doc.days, day_chains(doc), strict=True):
        route = day.route
        if route is not None and _same_points(route.points, chain):
            legs.extend(route.legs)
        else:
            legs.extend([None] * max(len(chain) - 1, 0))
    return legs


def copy_document(doc: PlanDocument) -> PlanDocument:
    """A friend's starting point: identical content and stop ids, so the copy compares as unchanged."""
    return doc.model_copy(deep=True)


def _stop_content(stop: PlanStop) -> dict:
    return stop.model_dump(mode="json", exclude={"id"})


def _stop_days(doc: PlanDocument) -> dict[str, tuple[int, PlanStop]]:
    return {stop.id: (index, stop) for index, day in enumerate(doc.days) for stop in day.stops}


def plan_km(doc: PlanDocument) -> float:
    """Straight-line km through every stop that has a place, in trip order (the PDF's fallback method)."""
    points = [(s.place.lat, s.place.lng) for s in doc.stops() if s.place is not None]
    meters = sum(haversine_m(a, b) for a, b in pairwise(points))
    return round(meters / 1000, 1)


def summarize(original: PlanDocument, doc: PlanDocument) -> PlanSummary:
    """Stops added / removed / changed vs the Original, matched by stop id. A move to another day is a change."""
    before = _stop_days(original)
    after = _stop_days(doc)
    added = after.keys() - before.keys()
    removed = before.keys() - after.keys()
    changed = [
        sid
        for sid in after.keys() & before.keys()
        if after[sid][0] != before[sid][0] or _stop_content(after[sid][1]) != _stop_content(before[sid][1])
    ]
    return PlanSummary(
        days=len(doc.days),
        stops=len(after),
        added=len(added),
        removed=len(removed),
        changed=len(changed),
        km=plan_km(doc),
    )


@dataclass
class ItemRow:
    position: int
    title: str
    place: PlanPlace | None
    start_time: time | None
    end_time: time | None
    transport: str | None
    accommodation: str | None
    notes: str | None
    links: list[str]


@dataclass
class DayRow:
    day_index: int
    day_date: date | None
    title: str | None
    notes: str | None
    items: list[ItemRow] = field(default_factory=list)


def apply_rows(doc: PlanDocument, start: date | None) -> list[DayRow]:
    """The itinerary rows a plan becomes. Days are dated from the trip start (requirements D-13)."""
    return [
        DayRow(
            day_index=index,
            day_date=start + timedelta(days=index) if start else None,
            title=day.title,
            notes=day.notes,
            items=[
                ItemRow(
                    position=position,
                    title=stop.title,
                    place=stop.place,
                    start_time=stop.start_time,
                    end_time=stop.end_time,
                    transport=stop.transport,
                    accommodation=stop.stay,
                    notes=stop.notes,
                    links=list(stop.links),
                )
                for position, stop in enumerate(day.stops)
            ],
        )
        for index, day in enumerate(doc.days)
    ]


def applied_end_date(start: date | None, current_end: date | None, day_count: int) -> date | None:
    """The trip end date after applying `day_count` days: start + days - 1, unchanged without a start."""
    if start is None or day_count == 0:
        return current_end
    return start + timedelta(days=day_count - 1)


def backups_to_prune(backups: Sequence[tuple[str, datetime]], keep: int = MAX_BACKUPS) -> list[str]:
    """Ids of the backups beyond the newest `keep` (oldest go first)."""
    newest_first = sorted(backups, key=lambda b: b[1], reverse=True)
    return [backup_id for backup_id, _ in newest_first[keep:]]
