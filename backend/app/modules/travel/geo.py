"""Pure geographic helpers (no DB, no I/O). Mirrored on the client only where a live preview needs it."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

EARTH_RADIUS_M = 6_371_008.8
COORD_DECIMALS = 5  # ~1 m; used for "same spot" dedup and polyline precision
_BBOX_MARGIN_DEG = 1e-9  # absorbs float rounding so the prefilter never drops a true match

Point = tuple[float, float]  # (lat, lng)


@dataclass(frozen=True)
class BBox:
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float
    # True when the box crosses the antimeridian: match lng >= min_lng OR lng <= max_lng.
    wraps: bool = False

    def contains(self, lat: float, lng: float) -> bool:
        if not self.min_lat <= lat <= self.max_lat:
            return False
        if self.wraps:
            return lng >= self.min_lng or lng <= self.max_lng
        return self.min_lng <= lng <= self.max_lng


def round_coord(value: float) -> float:
    return round(value, COORD_DECIMALS)


def haversine_m(a: Point, b: Point) -> float:
    lat1, lng1 = map(math.radians, a)
    lat2, lng2 = map(math.radians, b)
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(h)))


def bbox_for_radius(center: Point, radius_m: float) -> BBox:
    """A box guaranteed to contain every point within `radius_m` of `center` (a cheap SQL prefilter)."""
    lat, lng = center
    angular = radius_m / EARTH_RADIUS_M
    d_lat = math.degrees(angular) + _BBOX_MARGIN_DEG
    min_lat, max_lat = lat - d_lat, lat + d_lat
    if min_lat <= -90 or max_lat >= 90 or angular >= math.pi / 2:
        # A pole (or a hemisphere) is inside the circle: every longitude qualifies.
        return BBox(max(min_lat, -90.0), min(max_lat, 90.0), -180.0, 180.0)
    # Exact half-width in longitude of a spherical cap: asin(sin(d) / cos(lat)).
    ratio = math.sin(angular) / math.cos(math.radians(lat))
    if ratio >= 1:
        return BBox(min_lat, max_lat, -180.0, 180.0)
    d_lng = math.degrees(math.asin(ratio)) + _BBOX_MARGIN_DEG
    if d_lng >= 180:
        return BBox(min_lat, max_lat, -180.0, 180.0)
    min_lng, max_lng = lng - d_lng, lng + d_lng
    if min_lng < -180:
        return BBox(min_lat, max_lat, min_lng + 360, max_lng, wraps=True)
    if max_lng > 180:
        return BBox(min_lat, max_lat, min_lng, max_lng - 360, wraps=True)
    return BBox(min_lat, max_lat, min_lng, max_lng)


def within_radius(center: Point, point: Point, radius_m: float) -> bool:
    return haversine_m(center, point) <= radius_m


def path_length_m(points: Sequence[Point]) -> float:
    return sum(haversine_m(points[i], points[i + 1]) for i in range(len(points) - 1))


def elevation_gain_loss(elevations: Sequence[float]) -> tuple[float, float]:
    gain = loss = 0.0
    for prev, cur in zip(elevations, elevations[1:], strict=False):
        delta = cur - prev
        if delta > 0:
            gain += delta
        else:
            loss -= delta
    return gain, loss


def _perpendicular_m(p: Point, a: Point, b: Point) -> float:
    """Distance from p to segment ab on a local equirectangular projection (fine at track scale)."""
    ref_lat = math.radians((a[0] + b[0]) / 2)

    def xy(q: Point) -> tuple[float, float]:
        return (math.radians(q[1]) * math.cos(ref_lat) * EARTH_RADIUS_M, math.radians(q[0]) * EARTH_RADIUS_M)

    px, py = xy(p)
    ax, ay = xy(a)
    bx, by = xy(b)
    dx, dy = bx - ax, by - ay
    seg_sq = dx * dx + dy * dy
    if seg_sq == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg_sq))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def simplify_indices(points: Sequence[Point], tolerance_m: float) -> list[int]:
    """Douglas-Peucker (iterative). Returns kept indices, always including the first and last."""
    n = len(points)
    if n <= 2:
        return list(range(n))
    keep = [False] * n
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        start, end = stack.pop()
        best_i, best_d = -1, -1.0
        for i in range(start + 1, end):
            d = _perpendicular_m(points[i], points[start], points[end])
            if d > best_d:
                best_i, best_d = i, d
        if best_i != -1 and best_d > tolerance_m:
            keep[best_i] = True
            stack.append((start, best_i))
            stack.append((best_i, end))
    return [i for i, k in enumerate(keep) if k]


def simplify_dp(points: Sequence[Point], tolerance_m: float) -> list[Point]:
    return [points[i] for i in simplify_indices(points, tolerance_m)]


def _encode_value(value: int) -> str:
    value = ~(value << 1) if value < 0 else value << 1
    out = []
    while value >= 0x20:
        out.append(chr((0x20 | (value & 0x1F)) + 63))
        value >>= 5
    out.append(chr(value + 63))
    return "".join(out)


def encode_polyline(points: Sequence[Point]) -> str:
    """Google encoded polyline format at 1e-5 precision (the format Routes API returns)."""
    factor = 10**COORD_DECIMALS
    prev_lat = prev_lng = 0
    parts: list[str] = []
    for lat, lng in points:
        ilat, ilng = round(lat * factor), round(lng * factor)
        parts.append(_encode_value(ilat - prev_lat))
        parts.append(_encode_value(ilng - prev_lng))
        prev_lat, prev_lng = ilat, ilng
    return "".join(parts)


def decode_polyline(encoded: str, limit: int | None = None) -> list[Point]:
    """Decode a Google encoded polyline; `limit` stops after that many points (e.g. 1 for the start)."""
    factor = 10**COORD_DECIMALS
    points: list[Point] = []
    index = lat = lng = 0
    length = len(encoded)
    while index < length and (limit is None or len(points) < limit):
        deltas = []
        for _ in range(2):
            shift = result = 0
            while True:
                if index >= length:
                    raise ValueError("Truncated polyline")
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            deltas.append(~(result >> 1) if result & 1 else result >> 1)
        lat += deltas[0]
        lng += deltas[1]
        points.append((lat / factor, lng / factor))
    return points
