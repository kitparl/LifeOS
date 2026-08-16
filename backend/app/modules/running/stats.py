from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from app.modules.running.models import Run

DISTANCE_RANGES: dict[str, tuple[float, float, str]] = {
    "5k": (4.75, 5.25, "5K"),
    "10k": (9.5, 10.5, "10K"),
    "15k": (14.25, 15.75, "15K"),
    "half_marathon": (20.5, 21.5, "Half Marathon"),
    "marathon": (41.5, 43.0, "Marathon"),
}


def compute_pace(distance_km: float, duration_seconds: int) -> float:
    if distance_km <= 0:
        return 0.0
    return round(duration_seconds / 60 / distance_km, 2)


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def weekly_km(runs: list[Run], ref: date | None = None) -> float:
    ref = ref or datetime.now(timezone.utc).date()
    ws = _week_start(ref)
    we = ws + timedelta(days=6)
    total = sum(r.distance_km for r in runs if ws <= r.run_date <= we)
    return round(total, 2)


RACE_DISTANCE_KM_DEFAULTS: dict[str, float] = {
    "5k": 5.0,
    "10k": 10.0,
    "15k": 15.0,
    "half_marathon": 21.1,
    "marathon": 42.2,
}


def _race_distance_km(race) -> float:
    km = getattr(race, "distance_km", None)
    if km:
        return float(km)
    return RACE_DISTANCE_KM_DEFAULTS.get(getattr(race, "distance_type", "") or "", 0.0)


def compute_shoe_totals(runs: list[Run], races: list | None = None) -> list[dict]:
    """Aggregate distance / activity count / last date per shoe (runs + race events)."""
    buckets: dict[str, dict] = {}
    for r in runs:
        name = (getattr(r, "shoe", None) or "").strip()
        if not name:
            continue
        bucket = buckets.setdefault(
            name,
            {"shoe": name, "total_km": 0.0, "run_count": 0, "last_run_date": None},
        )
        bucket["total_km"] += r.distance_km
        bucket["run_count"] += 1
        if bucket["last_run_date"] is None or r.run_date > bucket["last_run_date"]:
            bucket["last_run_date"] = r.run_date
    for race in races or []:
        name = (getattr(race, "shoe", None) or "").strip()
        if not name:
            continue
        bucket = buckets.setdefault(
            name,
            {"shoe": name, "total_km": 0.0, "run_count": 0, "last_run_date": None},
        )
        bucket["total_km"] += _race_distance_km(race)
        bucket["run_count"] += 1
        if bucket["last_run_date"] is None or race.race_date > bucket["last_run_date"]:
            bucket["last_run_date"] = race.race_date
    results = []
    for name in sorted(buckets.keys(), key=str.lower):
        b = buckets[name]
        results.append(
            {
                "shoe": b["shoe"],
                "total_km": round(b["total_km"], 2),
                "run_count": b["run_count"],
                "last_run_date": b["last_run_date"],
            }
        )
    return results


def compute_event_stats(races: list, ref: date | None = None) -> dict:
    """Event attendance / distance / next-last summary for Running stats cards."""
    ref = ref or datetime.now(timezone.utc).date()
    year = ref.year
    attended = [r for r in races if getattr(r, "attended", False)]
    registered = [r for r in races if getattr(r, "registered", False)]
    past_or_today = [r for r in races if r.race_date <= ref]
    upcoming = [r for r in races if r.race_date >= ref]

    last_event = max(past_or_today, key=lambda r: r.race_date) if past_or_today else None
    next_event = min(upcoming, key=lambda r: r.race_date) if upcoming else None

    event_total_km = round(sum(_race_distance_km(r) for r in attended), 2)
    event_year_km = round(
        sum(_race_distance_km(r) for r in attended if r.race_date.year == year),
        2,
    )

    return {
        "events_attended": len(attended),
        "events_registered": len(registered),
        "last_event_name": last_event.name if last_event else None,
        "last_event_date": last_event.race_date if last_event else None,
        "next_event_name": next_event.name if next_event else None,
        "next_event_date": next_event.race_date if next_event else None,
        "event_total_km": event_total_km,
        "event_year_km": event_year_km,
        "event_year": year,
    }


@dataclass
class _PbCandidate:
    id: str
    activity_date: date
    distance_km: float
    duration_seconds: int
    source: str
    name: str | None


def _pb_candidates(runs: list[Run], races: list | None = None) -> list[_PbCandidate]:
    out: list[_PbCandidate] = []
    for r in runs:
        if not r.duration_seconds or r.distance_km <= 0:
            continue
        out.append(
            _PbCandidate(
                id=r.id,
                activity_date=r.run_date,
                distance_km=r.distance_km,
                duration_seconds=r.duration_seconds,
                source="run",
                name=None,
            )
        )
    for race in races or []:
        if getattr(race, "skipped", False):
            continue
        finish = getattr(race, "finish_time_seconds", None)
        km = _race_distance_km(race)
        if not finish or km <= 0:
            continue
        out.append(
            _PbCandidate(
                id=race.id,
                activity_date=race.race_date,
                distance_km=km,
                duration_seconds=int(finish),
                source="race",
                name=getattr(race, "name", None),
            )
        )
    return out


def _empty_pb(key: str, label: str) -> dict:
    return {
        "distance_type": key,
        "label": label,
        "run_id": None,
        "run_date": None,
        "distance_km": None,
        "pace_min_per_km": None,
        "duration_seconds": None,
        "source": None,
        "source_id": None,
        "source_name": None,
    }


def compute_personal_bests(runs: list[Run], races: list | None = None) -> list[dict]:
    candidates = _pb_candidates(runs, races)
    results = []
    for key, (lo, hi, label) in DISTANCE_RANGES.items():
        matching = [c for c in candidates if lo <= c.distance_km <= hi]
        if not matching:
            results.append(_empty_pb(key, label))
            continue
        best = min(matching, key=lambda c: compute_pace(c.distance_km, c.duration_seconds))
        results.append(
            {
                "distance_type": key,
                "label": label,
                "run_id": best.id if best.source == "run" else None,
                "run_date": best.activity_date,
                "distance_km": best.distance_km,
                "pace_min_per_km": compute_pace(best.distance_km, best.duration_seconds),
                "duration_seconds": best.duration_seconds,
                "source": best.source,
                "source_id": best.id,
                "source_name": best.name if best.source == "race" else "Log run",
            }
        )
    return results


def compute_distance_over_time(runs: list[Run], races: list | None = None, limit: int = 30) -> list[dict]:
    points: list[tuple[date, float]] = []
    for r in runs:
        points.append((r.run_date, float(r.distance_km)))
    for race in races or []:
        if not getattr(race, "attended", False):
            continue
        km = _race_distance_km(race)
        if km > 0:
            points.append((race.race_date, km))
    points.sort(key=lambda p: p[0])
    points = points[-limit:]
    return [{"label": d.isoformat(), "value": round(km, 2)} for d, km in points]


def compute_weekly_totals(runs: list[Run], races: list | None = None, weeks: int = 12) -> list[dict]:
    buckets: dict[date, float] = {}

    def add(d: date, km: float) -> None:
        ws = _week_start(d)
        buckets[ws] = buckets.get(ws, 0.0) + km

    for r in runs:
        add(r.run_date, float(r.distance_km))
    for race in races or []:
        if getattr(race, "attended", False):
            add(race.race_date, _race_distance_km(race))

    today = datetime.now(timezone.utc).date()
    current = _week_start(today)
    series = []
    for i in range(weeks - 1, -1, -1):
        ws = current - timedelta(days=7 * i)
        series.append({"label": ws.isoformat(), "value": round(buckets.get(ws, 0.0), 2)})
    return series
