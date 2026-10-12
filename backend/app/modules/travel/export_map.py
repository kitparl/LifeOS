"""Small schematic maps for the PDF guide, drawn from coordinates alone (no tiles, no Google calls)."""

from __future__ import annotations

import math
from collections.abc import Sequence

from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth

from app.modules.travel.geo import Point

PAPER = colors.HexColor("#eef3f6")
GRID = colors.HexColor("#dde6ec")
INK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#5f6c7b")
DAY_COLORS = [colors.HexColor(c) for c in ("#0f6b8f", "#c2410c", "#15803d", "#7c3aed", "#b45309", "#be185d")]
M_PER_DEG = 111_195.0
MIN_SPAN_DEG = 0.02
PAD = 22


def day_color(day_index: int) -> colors.Color:
    return DAY_COLORS[day_index % len(DAY_COLORS)]


class _Frame:
    """Fits lat/lng points into a width x height box (equirectangular, aspect kept)."""

    def __init__(self, points: Sequence[Point], width: float, height: float):
        lats = [p[0] for p in points]
        lngs = [p[1] for p in points]
        mid_lat = (min(lats) + max(lats)) / 2
        self.cos = math.cos(math.radians(mid_lat))
        span_y = max(max(lats) - min(lats), MIN_SPAN_DEG)
        span_x = max((max(lngs) - min(lngs)) * self.cos, MIN_SPAN_DEG)
        self.scale = min((width - 2 * PAD) / span_x, (height - 2 * PAD) / span_y)  # drawing units per degree of lat
        self.cx = (min(lngs) + max(lngs)) / 2
        self.cy = mid_lat
        self.width, self.height = width, height

    def xy(self, point: Point) -> tuple[float, float]:
        return (
            self.width / 2 + (point[1] - self.cx) * self.cos * self.scale,
            self.height / 2 + (point[0] - self.cy) * self.scale,
        )


def _base(width: float, height: float) -> Drawing:
    drawing = Drawing(width, height)
    drawing.add(Rect(0, 0, width, height, fillColor=PAPER, strokeColor=GRID, strokeWidth=0.8))
    for i in range(1, 6):
        drawing.add(Line(width * i / 6, 0, width * i / 6, height, strokeColor=GRID, strokeWidth=0.4))
    for i in range(1, 3):
        drawing.add(Line(0, height * i / 3, width, height * i / 3, strokeColor=GRID, strokeWidth=0.4))
    return drawing


def _decorate(drawing: Drawing, frame: _Frame) -> None:
    """North arrow and a scale bar rounded to a friendly number of km."""
    width, height = frame.width, frame.height
    km_per_unit = 1 / (frame.scale / (M_PER_DEG / 1000))
    target = width * 0.22 * km_per_unit
    nice = max((v for v in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000) if v <= target), default=0.1)
    length = nice / km_per_unit
    drawing.add(Line(10, 10, 10 + length, 10, strokeColor=INK, strokeWidth=1.2))
    drawing.add(Line(10, 7, 10, 13, strokeColor=INK, strokeWidth=1.2))
    drawing.add(Line(10 + length, 7, 10 + length, 13, strokeColor=INK, strokeWidth=1.2))
    drawing.add(String(10 + length + 4, 8, f"{nice:g} km", fontSize=7, fontName="Helvetica", fillColor=MUTED))
    drawing.add(Line(width - 14, height - 28, width - 14, height - 12, strokeColor=INK, strokeWidth=1.2))
    drawing.add(String(width - 17.5, height - 9, "N", fontSize=8, fontName="Helvetica-Bold", fillColor=INK))


def _path(drawing: Drawing, frame: _Frame, path: Sequence[Point], color: colors.Color) -> None:
    coords = [c for p in path for c in frame.xy(p)]
    drawing.add(PolyLine(coords, strokeColor=colors.white, strokeWidth=4.2, strokeLineJoin=1, strokeLineCap=1))
    drawing.add(PolyLine(coords, strokeColor=color, strokeWidth=2, strokeLineJoin=1, strokeLineCap=1))


def _pin(drawing: Drawing, x: float, y: float, label: str, color: colors.Color, hollow: bool = False) -> None:
    radius = 6.2 if len(label) < 3 else 8
    drawing.add(Circle(x, y, radius, fillColor=colors.white if hollow else color, strokeColor=color, strokeWidth=1.6))
    if label:
        drawing.add(
            String(
                x,
                y - 2.6,
                label,
                fontSize=7,
                fontName="Helvetica-Bold",
                textAnchor="middle",
                fillColor=color if hollow else colors.white,
            )
        )


def _caption(
    drawing: Drawing, frame: _Frame, x: float, y: float, name: str, taken: list[tuple[float, float, float]]
) -> None:
    text = name if len(name) <= 24 else name[:23].rstrip() + "..."
    w = stringWidth(text, "Helvetica", 7) + 6
    left = x + 9 + w > frame.width - 4
    bx = x - 9 - w if left else x + 9
    by = y - 4
    for tx, ty, tw in taken:  # nudge down while it would sit on top of another caption
        if abs(by - ty) < 9 and bx < tx + tw and tx < bx + w:
            by = ty - 10
    taken.append((bx, by, w))
    drawing.add(Rect(bx, by, w, 10, fillColor=colors.white, strokeColor=None, fillOpacity=0.85))
    drawing.add(String(bx + 3, by + 2.6, text, fontSize=7, fontName="Helvetica", fillColor=INK))


def day_map(
    pins: Sequence[tuple[Point, str, str]],
    path: Sequence[Point],
    color: colors.Color,
    width: float,
    height: float = 190,
    start: tuple[Point, str] | None = None,
) -> Drawing | None:
    """One day: `pins` are (point, number label, name); `start` is yesterday's last stop, drawn hollow."""
    points = [p for p, _, _ in pins] + ([start[0]] if start else []) + list(path)
    if not points:
        return None
    frame = _Frame(points, width, height)
    drawing = _base(width, height)
    if len(path) > 1:
        _path(drawing, frame, path, color)
    taken: list[tuple[float, float, float]] = []
    if start:
        x, y = frame.xy(start[0])
        _pin(drawing, x, y, "", color, hollow=True)
        _caption(drawing, frame, x, y, f"From {start[1]}", taken)
    for point, label, name in pins:
        x, y = frame.xy(point)
        _pin(drawing, x, y, label, color)
        _caption(drawing, frame, x, y, name, taken)
    _decorate(drawing, frame)
    return drawing


def overview_map(
    days: Sequence[tuple[int, Sequence[Point], Sequence[Point]]], width: float, height: float = 230
) -> Drawing | None:
    """Whole trip: for each (day index, path, stop points) the path in that day's colour, a dot per stop, a "D#" badge."""
    points = [p for _, path, stops in days for p in (*path, *stops)]
    if not points:
        return None
    frame = _Frame(points, width, height)
    drawing = _base(width, height)
    for index, path, _ in days:
        if len(path) > 1:
            _path(drawing, frame, path, day_color(index))
    for index, _path_points, stops in days:
        for point in stops:
            x, y = frame.xy(point)
            drawing.add(Circle(x, y, 3, fillColor=colors.white, strokeColor=day_color(index), strokeWidth=1.4))
    for index, _, stops in days:
        if stops:
            x, y = frame.xy(stops[0])
            _pin(drawing, x, y + 11, f"D{index + 1}", day_color(index))
    _decorate(drawing, frame)
    return drawing
