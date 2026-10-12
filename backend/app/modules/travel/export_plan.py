"""Per-day facts for the PDF guide: stops in order, km and time between them, where the night is spent.

Pure (no DB, no PDF). Distances use the saved route's road legs when they still match the stops;
otherwise they are straight-line estimates and every figure is flagged `approx`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.travel.geo import Point, decode_polyline, haversine_m
from app.modules.travel.models import TravelPlace
from app.modules.travel.schemas.trips import DayOut, ItemOut, TripDetail


@dataclass
class Leg:
    """Getting from the previous stop of the trip to this one."""

    from_name: str
    meters: float
    seconds: int | None
    path: list[Point]
    approx: bool


@dataclass
class PlannedItem:
    number: int
    item: ItemOut
    place: TravelPlace | None
    leg: Leg | None = None


@dataclass
class DayPlan:
    day: DayOut
    items: list[PlannedItem] = field(default_factory=list)
    stay: list[str] = field(default_factory=list)
    previous: Point | None = None
    previous_name: str | None = None

    @property
    def legs(self) -> list[Leg]:
        return [i.leg for i in self.items if i.leg]

    @property
    def meters(self) -> float:
        return sum(leg.meters for leg in self.legs)

    @property
    def seconds(self) -> int | None:
        legs = self.legs
        return sum(leg.seconds or 0 for leg in legs) if legs and all(leg.seconds for leg in legs) else None

    @property
    def approx(self) -> bool:
        return any(leg.approx for leg in self.legs)

    @property
    def points(self) -> list[Point]:
        """Where the day starts (yesterday's last stop, if any) and each place visited, in order."""
        pts = [self.previous] if self.previous and self.legs else []
        return pts + [(i.place.lat, i.place.lng) for i in self.items if i.place]


@dataclass
class TripPlan:
    days: list[DayPlan]
    meters: float
    seconds: int | None
    approx: bool


def build_trip_plan(detail: TripDetail, places: dict[str, TravelPlace]) -> TripPlan:
    route = detail.route
    stops = detail.stops
    road_legs = (
        route.legs if route and not route.is_stale and route.legs and len(route.legs) == len(stops) - 1 else None
    )

    current = -1  # index into `stops`, advanced exactly like the backend's stop_sequence
    last: tuple[str, Point] | None = None
    days: list[DayPlan] = []
    for day in detail.days:
        plan = DayPlan(day=day)
        if last:
            plan.previous_name, plan.previous = last
        for number, item in enumerate(sorted(day.items, key=lambda i: i.position), 1):
            place = places.get(item.place_id) if item.place_id else None
            planned = PlannedItem(number=number, item=item, place=place)
            if place is not None:
                if current < 0 or stops[current].place_id != place.id:
                    current += 1
                    if last is not None:
                        planned.leg = _leg(last, place, road_legs[current - 1] if road_legs else None)
                last = (place.name, (place.lat, place.lng))
            plan.items.append(planned)
            if item.accommodation and item.accommodation not in plan.stay:
                plan.stay.append(item.accommodation)
        days.append(plan)

    legs = [leg for d in days for leg in d.legs]
    seconds = sum(leg.seconds or 0 for leg in legs) if legs and all(leg.seconds for leg in legs) else None
    return TripPlan(days, sum(leg.meters for leg in legs), seconds, any(leg.approx for leg in legs))


def _leg(last: tuple[str, Point], place: TravelPlace, road) -> Leg:
    start = last[1]
    end = (place.lat, place.lng)
    if road is not None:
        path = decode_polyline(road.polyline) if road.polyline else [start, end]
        return Leg(last[0], road.distance_m, road.duration_s, path, approx=False)
    return Leg(last[0], haversine_m(start, end), None, [start, end], approx=True)
