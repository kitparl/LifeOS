"""Pure itinerary rules. The map and the itinerary both read `stop_sequence`, so they cannot drift (spec §12)."""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass


class InvalidOrder(ValueError):
    """The requested order does not contain exactly the trip's items and days."""


@dataclass(frozen=True)
class ItemRef:
    id: str
    day_id: str
    position: int
    place_id: str | None


@dataclass(frozen=True)
class Stop:
    place_id: str
    day_id: str
    name: str
    lat: float
    lng: float


def apply_order(
    day_ids: Iterable[str],
    items: Iterable[ItemRef],
    requested: Mapping[str, Sequence[str]],
) -> dict[str, tuple[str, int]]:
    """Validate a full `{day_id: [item_id, ...]}` layout and return `{item_id: (day_id, position)}`.

    The request must mention only the trip's days and contain every item exactly once, so a
    drag can move items between days but never lose or duplicate one. Positions become 0..n-1.
    """
    known_days = set(day_ids)
    unknown = set(requested) - known_days
    if unknown:
        raise InvalidOrder("Unknown day in the requested order")
    current = Counter(item.id for item in items)
    wanted = Counter(item_id for ids in requested.values() for item_id in ids)
    if wanted != current:
        raise InvalidOrder("The order must list every itinerary item exactly once")
    return {item_id: (day_id, index) for day_id, ids in requested.items() for index, item_id in enumerate(ids)}


def stop_sequence(
    day_order: Sequence[str],
    items: Iterable[ItemRef],
    places: Mapping[str, tuple[str, float, float]],
) -> list[Stop]:
    """Ordered stops (day order, then position) for the map and route; consecutive repeats collapse."""
    day_rank = {day_id: i for i, day_id in enumerate(day_order)}
    ordered = sorted(
        (i for i in items if i.place_id in places and i.day_id in day_rank),
        key=lambda i: (day_rank[i.day_id], i.position),
    )
    stops: list[Stop] = []
    for item in ordered:
        place_id = item.place_id
        if place_id is None or (stops and stops[-1].place_id == place_id):
            continue
        name, lat, lng = places[place_id]
        stops.append(Stop(place_id=place_id, day_id=item.day_id, name=name, lat=lat, lng=lng))
    return stops


def stops_fingerprint(stops: Sequence[Stop], mode: str) -> str:
    """Changes whenever stop order, a stop's position, or the mode changes — the route is then stale."""
    raw = mode + "|" + ";".join(f"{s.place_id}@{s.lat:.5f},{s.lng:.5f}" for s in stops)
    return hashlib.sha256(raw.encode()).hexdigest()
