from datetime import UTC, date, datetime, timedelta

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
    ref = ref or datetime.now(UTC).date()
    ws = _week_start(ref)
    we = ws + timedelta(days=6)
    total = sum(r.distance_km for r in runs if ws <= r.run_date <= we)
    return round(total, 2)


def compute_personal_bests(runs: list[Run]) -> list[dict]:
    results = []
    for key, (lo, hi, label) in DISTANCE_RANGES.items():
        matching = [r for r in runs if lo <= r.distance_km <= hi]
        if not matching:
            results.append(
                {
                    "distance_type": key,
                    "label": label,
                    "run_id": None,
                    "run_date": None,
                    "distance_km": None,
                    "pace_min_per_km": None,
                    "duration_seconds": None,
                }
            )
            continue
        best = min(matching, key=lambda r: compute_pace(r.distance_km, r.duration_seconds))
        results.append(
            {
                "distance_type": key,
                "label": label,
                "run_id": best.id,
                "run_date": best.run_date,
                "distance_km": best.distance_km,
                "pace_min_per_km": compute_pace(best.distance_km, best.duration_seconds),
                "duration_seconds": best.duration_seconds,
            }
        )
    return results
