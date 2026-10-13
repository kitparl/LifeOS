"""Per-day facts for the PDF guide: stops in order, km and time between them, where the night is spent.

Pure (no DB, no PDF). Distances use the saved route's road legs when they still match the stops;
otherwise they are straight-line estimates and every figure is flagged `approx`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from app.modules.travel.geo import Point, decode_polyline, haversine_m
from app.modules.travel.itinerary import ItemRef, stop_sequence
from app.modules.travel.models import TravelPlace
from app.modules.travel.schemas.plan_document import PlanDocument
from app.modules.travel.schemas.trips import DayOut, ItemOut, StopOut, TripDetail, TripPlaceOut, TripSummary


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


def plan_document_detail(trip: TripSummary, doc: PlanDocument) -> tuple[TripDetail, dict[str, TravelPlace]]:
    """A shared plan in the shape the PDF guide reads, with unsaved places (so any version can be exported).

    No saved route: every distance is a straight-line estimate, flagged `approx` like any stale route.
    """
    places: dict[str, TravelPlace] = {}
    keys: dict[tuple, str] = {}
    days: list[DayOut] = []
    refs: list[ItemRef] = []
    for d_index, day in enumerate(doc.days):
        day_id = f"d{d_index}"
        items: list[ItemOut] = []
        for position, stop in enumerate(day.stops):
            place_id = None
            if stop.place is not None:
                key = (stop.place.google_place_id or "", stop.place.lat, stop.place.lng)
                place_id = keys.setdefault(key, f"p{len(keys)}")
                places.setdefault(
                    place_id,
                    TravelPlace(
                        id=place_id,
                        name=stop.place.name,
                        lat=stop.place.lat,
                        lng=stop.place.lng,
                        external_place_id=stop.place.google_place_id,
                    ),
                )
            item = ItemOut(
                id=stop.id,
                day_id=day_id,
                position=position,
                place_id=place_id,
                title=stop.title,
                start_time=stop.start_time,
                end_time=stop.end_time,
                transport=stop.transport,
                accommodation=stop.stay,
                notes=stop.notes,
                links=list(stop.links),
            )
            items.append(item)
            refs.append(ItemRef(id=item.id, day_id=day_id, position=position, place_id=place_id))
        day_date = trip.start_date + timedelta(days=d_index) if trip.start_date else None
        days.append(DayOut(id=day_id, day_index=d_index, day_date=day_date, title=day.title, notes=day.notes, items=items))
    stops = stop_sequence(
        [d.id for d in days], refs, {pid: (p.name, p.lat, p.lng) for pid, p in places.items()}
    )
    detail = TripDetail(
        trip=trip,
        days=days,
        places=[
            TripPlaceOut(id=p.id, name=p.name, lat=p.lat, lng=p.lng, status="planned", external_place_id=p.external_place_id)
            for p in places.values()
        ],
        stops=[StopOut(place_id=s.place_id, day_id=s.day_id, name=s.name, lat=s.lat, lng=s.lng) for s in stops],
        route=None,
    )
    return detail, places
