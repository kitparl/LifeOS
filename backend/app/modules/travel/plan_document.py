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

from app.modules.travel.geo import haversine_m
from app.modules.travel.models import TravelPlace
from app.modules.travel.schemas.plan_document import PlanDay, PlanDocument, PlanPlace, PlanStop
from app.modules.travel.schemas.shares import PlanSummary
from app.modules.travel.schemas.trips import DayOut

MAX_BACKUPS = 5


def new_stop_id() -> str:
    return str(uuid.uuid4())


def snapshot_from_trip(days: Sequence[DayOut], places: Mapping[str, TravelPlace]) -> PlanDocument:
    """The trip's days and stops as a plan. Only itinerary fields; trip notes, photos etc. never enter."""
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
    return PlanDocument(days=plan_days)


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
