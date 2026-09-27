"""GPX 1.0/1.1 import and export (spec §16). Pure: bytes in, dataclasses out.

Parsing uses `defusedxml`, which refuses DTDs, entity expansion and external references
(XXE / billion-laughs, SECURITY-13). Size and point caps bound memory and CPU.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring  # building only; parsing is defused

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import ParseError, fromstring

MAX_GPX_BYTES = 10 * 1024 * 1024
MAX_GPX_POINTS = 100_000
MAX_GPX_WAYPOINTS = 500
GPX_NS = "http://www.topografix.com/GPX/1/1"


class GpxError(ValueError):
    """The upload is not a usable GPX file; the message is safe to show the user."""


@dataclass(frozen=True)
class GpxWaypoint:
    name: str
    lat: float
    lng: float
    elevation: float | None = None


@dataclass(frozen=True)
class GpxTrack:
    name: str | None
    points: list[tuple[float, float]]
    elevations: list[float | None]
    times: list[datetime | None]
    waypoints: list[GpxWaypoint] = field(default_factory=list)

    @property
    def has_elevation(self) -> bool:
        return bool(self.elevations) and all(e is not None for e in self.elevations)

    @property
    def has_time(self) -> bool:
        return any(t is not None for t in self.times)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(el: Element, name: str) -> str | None:
    for child in el:
        if _local(child.tag) == name:
            return (child.text or "").strip() or None
    return None


def _coord(el: Element) -> tuple[float, float]:
    try:
        lat, lng = float(el.attrib["lat"]), float(el.attrib["lon"])
    except (KeyError, ValueError) as exc:
        raise GpxError("A point is missing valid lat/lon") from exc
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise GpxError("A point has coordinates out of range")
    return lat, lng


def _float(text: str | None) -> float | None:
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _time(text: str | None) -> datetime | None:
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_gpx(data: bytes) -> GpxTrack:
    if len(data) > MAX_GPX_BYTES:
        raise GpxError("GPX file is larger than 10 MB")
    try:
        root = fromstring(data, forbid_dtd=True)
    except (ParseError, DefusedXmlException, ValueError) as exc:
        raise GpxError("This is not a valid GPX file") from exc
    if _local(root.tag) != "gpx":
        raise GpxError("This is not a GPX file")

    name: str | None = None
    track_points: list[Element] = []
    route_points: list[Element] = []
    waypoints: list[GpxWaypoint] = []
    for el in root.iter():
        tag = _local(el.tag)
        if tag == "trkpt":
            track_points.append(el)
        elif tag == "rtept":
            route_points.append(el)
        elif tag == "wpt":
            if len(waypoints) >= MAX_GPX_WAYPOINTS:
                raise GpxError(f"GPX has more than {MAX_GPX_WAYPOINTS} waypoints")
            lat, lng = _coord(el)
            waypoints.append(
                GpxWaypoint(
                    name=(_child_text(el, "name") or "Waypoint")[:120],
                    lat=lat,
                    lng=lng,
                    elevation=_float(_child_text(el, "ele")),
                )
            )
        elif tag in ("trk", "rte") and name is None:
            name = _child_text(el, "name")
        if len(track_points) + len(route_points) > MAX_GPX_POINTS:
            raise GpxError(f"GPX has more than {MAX_GPX_POINTS:,} points")

    source = track_points or route_points  # prefer the recorded track over a planned route
    if len(source) < 2:
        raise GpxError("GPX needs a track or route with at least two points")
    raw_name = name or _child_text(root, "name")  # GPX 1.0 keeps the file name directly under <gpx>
    return GpxTrack(
        name=raw_name[:200] if raw_name else None,
        points=[_coord(p) for p in source],
        elevations=[_float(_child_text(p, "ele")) for p in source],
        times=[_time(_child_text(p, "time")) for p in source],
        waypoints=waypoints,
    )


def build_gpx(
    name: str,
    points: list[tuple[float, float]],
    waypoints: list[GpxWaypoint] | None = None,
    elevations: list[float | None] | None = None,
) -> bytes:
    """GPX 1.1 with one track segment (+ waypoints). Values are escaped by ElementTree."""
    root = Element("gpx", {"version": "1.1", "creator": "LifeOS Travel", "xmlns": GPX_NS})
    for wp in waypoints or []:
        w = SubElement(root, "wpt", {"lat": f"{wp.lat:.7f}", "lon": f"{wp.lng:.7f}"})
        if wp.elevation is not None:
            SubElement(w, "ele").text = f"{wp.elevation:.1f}"
        SubElement(w, "name").text = wp.name
    trk = SubElement(root, "trk")
    SubElement(trk, "name").text = name
    seg = SubElement(trk, "trkseg")
    for i, (lat, lng) in enumerate(points):
        pt = SubElement(seg, "trkpt", {"lat": f"{lat:.7f}", "lon": f"{lng:.7f}"})
        ele = elevations[i] if elevations and i < len(elevations) else None
        if ele is not None:
            SubElement(pt, "ele").text = f"{ele:.1f}"
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(root, encoding="utf-8")
