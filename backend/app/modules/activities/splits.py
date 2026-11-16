"""Pure helpers for activity data: route polyline, series packing, per-km splits, downsampling."""

import gzip
import json
from dataclasses import dataclass

from app.modules.activities.contracts import ParsedSeries

SPLIT_DISTANCE_M = 1000.0
# A final partial split is only reported when at least this much distance is left over.
MIN_PARTIAL_SPLIT_M = 50.0

_SERIES_CHANNELS = ("distance_m", "lat", "lon", "altitude_m", "heart_rate", "cadence", "speed_mps")


# --- Route polyline (standard encoded-polyline algorithm, 5 decimal places) -----------------------


def _encode_number(value: int) -> str:
    value = ~(value << 1) if value < 0 else value << 1
    out = []
    while value >= 0x20:
        out.append(chr((0x20 | (value & 0x1F)) + 63))
        value >>= 5
    out.append(chr(value + 63))
    return "".join(out)


def encode_polyline(points: list[tuple[float, float]]) -> str:
    out = []
    prev_lat = prev_lon = 0
    for lat, lon in points:
        lat_i, lon_i = round(lat * 1e5), round(lon * 1e5)
        out.append(_encode_number(lat_i - prev_lat))
        out.append(_encode_number(lon_i - prev_lon))
        prev_lat, prev_lon = lat_i, lon_i
    return "".join(out)


def decode_polyline(encoded: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    index = lat = lon = 0
    while index < len(encoded):
        deltas = []
        for _ in range(2):
            shift = result = 0
            while True:
                byte = ord(encoded[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break
            deltas.append(~(result >> 1) if result & 1 else result >> 1)
        lat += deltas[0]
        lon += deltas[1]
        points.append((lat / 1e5, lon / 1e5))
    return points


# --- Series packing (gzip JSON; never pickle) -----------------------------------------------------


def pack_series(series: ParsedSeries) -> bytes:
    payload = {"time_s": series.time_s, "extras": series.extras}
    for name in _SERIES_CHANNELS:
        payload[name] = getattr(series, name)
    return gzip.compress(json.dumps(payload, separators=(",", ":")).encode("utf-8"))


def unpack_series(data: bytes) -> ParsedSeries:
    payload = json.loads(gzip.decompress(data).decode("utf-8"))
    return ParsedSeries(
        time_s=payload["time_s"],
        extras=payload.get("extras") or {},
        **{name: payload.get(name) for name in _SERIES_CHANNELS},
    )


# --- Downsampling ---------------------------------------------------------------------------------


def downsample_indices(count: int, limit: int) -> list[int]:
    """Evenly spaced indices into a list of `count` items: at most `limit`, always first and last."""
    if count <= 0 or limit <= 0:
        return []
    if count <= limit:
        return list(range(count))
    if limit == 1:
        return [0]
    step = (count - 1) / (limit - 1)
    return sorted({round(i * step) for i in range(limit)})


def route_points(series: ParsedSeries, limit: int) -> list[tuple[float, float]]:
    """Samples that have a position, reduced to at most `limit` points."""
    if not series.lat or not series.lon:
        return []
    pairs = [(a, b) for a, b in zip(series.lat, series.lon, strict=True) if a is not None and b is not None]
    return [pairs[i] for i in downsample_indices(len(pairs), limit)]


# --- Per-km splits --------------------------------------------------------------------------------


@dataclass(frozen=True)
class Split:
    index: int
    distance_m: float
    duration_s: float
    pace_s_per_km: float | None
    avg_hr: float | None
    elevation_change_m: float | None
    avg_cadence: float | None


def _interpolate(xs: list[float], ys: list[float | None], x: float) -> float | None:
    """Linear value of ys at x (xs ascending); None when either bracketing value is missing."""
    hi = next((i for i, v in enumerate(xs) if v >= x), len(xs) - 1)
    if hi == 0 or xs[hi] == x:
        return ys[hi]
    lo = hi - 1
    if ys[lo] is None or ys[hi] is None:
        return None
    span = xs[hi] - xs[lo]
    return ys[hi] if span == 0 else ys[lo] + (ys[hi] - ys[lo]) * (x - xs[lo]) / span


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def compute_km_splits(series: ParsedSeries) -> list[Split]:
    """One split per full 1000 m of recorded distance (time interpolated at the boundary) plus a partial last split."""
    if not series.distance_m:
        return []
    rows = []  # (distance, time, hr, altitude, cadence) for samples with a distance, never going backwards
    last_d = -1.0
    for i, d in enumerate(series.distance_m):
        if d is None or d < last_d:
            continue
        last_d = d
        rows.append(
            (
                d,
                float(series.time_s[i]),
                series.heart_rate[i] if series.heart_rate else None,
                series.altitude_m[i] if series.altitude_m else None,
                series.cadence[i] if series.cadence else None,
            )
        )
    if len(rows) < 2:
        return []
    dist = [r[0] for r in rows]
    time = [r[1] for r in rows]
    alt = [r[3] for r in rows]
    total = dist[-1]
    full = int(total // SPLIT_DISTANCE_M)
    boundaries = [k * SPLIT_DISTANCE_M for k in range(full + 1)]
    if total - boundaries[-1] >= MIN_PARTIAL_SPLIT_M:
        boundaries.append(total)

    splits = []
    for k in range(1, len(boundaries)):
        start_d, end_d = boundaries[k - 1], boundaries[k]
        start_t = _interpolate(dist, time, start_d)
        end_t = _interpolate(dist, time, end_d)
        duration = (end_t or 0.0) - (start_t or 0.0)
        inside = [r for r in rows if start_d < r[0] <= end_d]
        start_alt = _interpolate(dist, alt, start_d)
        end_alt = _interpolate(dist, alt, end_d)
        length = end_d - start_d
        splits.append(
            Split(
                index=k,
                distance_m=length,
                duration_s=duration,
                pace_s_per_km=duration / (length / 1000.0) if duration > 0 else None,
                avg_hr=_mean([r[2] for r in inside if r[2] is not None]),
                elevation_change_m=None if start_alt is None or end_alt is None else end_alt - start_alt,
                avg_cadence=_mean([r[4] for r in inside if r[4] is not None]),
            )
        )
    return splits
