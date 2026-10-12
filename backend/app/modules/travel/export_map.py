"""Maps for the PDF guide: real map tiles underneath when available, a plain schematic otherwise."""

from __future__ import annotations

from collections.abc import Sequence

from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable

from app.modules.travel.export_tiles import MercFrame, TileBasemap
from app.modules.travel.geo import Point

PAPER = colors.HexColor("#eef3f6")
GRID = colors.HexColor("#dde6ec")
INK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#5f6c7b")
DAY_COLORS = [colors.HexColor(c) for c in ("#0f6b8f", "#c2410c", "#15803d", "#7c3aed", "#b45309", "#be185d")]
DASH = [5, 3]


class MapView(Flowable):
    """A map: the tile image (when there is one) underneath, the route and pins drawn on top."""

    def __init__(self, drawing: Drawing, image: object | None = None):
        super().__init__()
        self.drawing, self.image = drawing, image
        self.width, self.height = drawing.width, drawing.height

    def wrap(self, avail_width: float, avail_height: float) -> tuple[float, float]:
        return self.width, self.height

    def draw(self) -> None:
        if self.image is not None:
            self.canv.drawImage(self.image, 0, 0, self.width, self.height)
        renderPDF.draw(self.drawing, self.canv, 0, 0)


def day_color(day_index: int) -> colors.Color:
    return DAY_COLORS[day_index % len(DAY_COLORS)]


def _base(frame: MercFrame, basemap: TileBasemap | None) -> tuple[Drawing, object | None]:
    """The drawing to put pins on, and the tile image to put under it (None: schematic background)."""
    width, height = frame.width, frame.height
    drawing = Drawing(width, height)
    image = basemap.render(frame) if basemap else None
    if image is not None:
        drawing.add(Rect(0, 0, width, height, fillColor=None, strokeColor=GRID, strokeWidth=0.8))
        _label(drawing, width - 4, 3, basemap.attribution, anchor="end")
        return drawing, image
    drawing.add(Rect(0, 0, width, height, fillColor=PAPER, strokeColor=GRID, strokeWidth=0.8))
    for i in range(1, 6):
        drawing.add(Line(width * i / 6, 0, width * i / 6, height, strokeColor=GRID, strokeWidth=0.4))
    for i in range(1, 3):
        drawing.add(Line(0, height * i / 3, width, height * i / 3, strokeColor=GRID, strokeWidth=0.4))
    return drawing, None


def _label(drawing: Drawing, x: float, y: float, text: str, anchor: str = "start") -> None:
    if not text:
        return
    w = stringWidth(text, "Helvetica", 6) + 4
    left = x - w + 2 if anchor == "end" else x - 2
    drawing.add(Rect(left, y - 2, w, 9, fillColor=colors.white, strokeColor=None, fillOpacity=0.8))
    drawing.add(String(x, y, text, fontSize=6, fontName="Helvetica", textAnchor=anchor, fillColor=MUTED))


def _decorate(drawing: Drawing, frame: MercFrame) -> None:
    """North arrow and a scale bar rounded to a friendly number of km."""
    width, height = frame.width, frame.height
    target = width * 0.22 * frame.km_per_pt
    nice = max((v for v in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000) if v <= target), default=0.1)
    length = nice / frame.km_per_pt
    drawing.add(Rect(6, 14, length + 38, 14, fillColor=colors.white, strokeColor=None, fillOpacity=0.8))
    drawing.add(Line(10, 19, 10 + length, 19, strokeColor=INK, strokeWidth=1.2))
    drawing.add(Line(10, 16, 10, 22, strokeColor=INK, strokeWidth=1.2))
    drawing.add(Line(10 + length, 16, 10 + length, 22, strokeColor=INK, strokeWidth=1.2))
    drawing.add(String(10 + length + 4, 17, f"{nice:g} km", fontSize=7, fontName="Helvetica", fillColor=MUTED))
    drawing.add(Rect(width - 24, height - 34, 20, 30, fillColor=colors.white, strokeColor=None, fillOpacity=0.8))
    drawing.add(Line(width - 14, height - 30, width - 14, height - 16, strokeColor=INK, strokeWidth=1.2))
    drawing.add(String(width - 17.5, height - 13, "N", fontSize=8, fontName="Helvetica-Bold", fillColor=INK))


def _path(drawing: Drawing, frame: MercFrame, path: Sequence[Point], color: colors.Color, dashed: bool) -> None:
    coords = [c for p in path for c in frame.xy(p)]
    drawing.add(PolyLine(coords, strokeColor=colors.white, strokeWidth=5, strokeLineJoin=1, strokeLineCap=1))
    drawing.add(
        PolyLine(
            coords,
            strokeColor=color,
            strokeWidth=2.4,
            strokeLineJoin=1,
            strokeLineCap=1,
            strokeDashArray=DASH if dashed else None,
        )
    )


def _pin(drawing: Drawing, x: float, y: float, label: str, color: colors.Color, hollow: bool = False) -> None:
    radius = 6.2 if len(label) < 3 else 8
    drawing.add(Circle(x, y, radius + 1.6, fillColor=colors.white, strokeColor=None))
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
    drawing: Drawing, frame: MercFrame, x: float, y: float, name: str, taken: list[tuple[float, float, float]]
) -> None:
    text = name if len(name) <= 24 else name[:23].rstrip() + "..."
    w = stringWidth(text, "Helvetica", 7) + 6
    left = x + 10 + w > frame.width - 4
    bx = x - 10 - w if left else x + 10
    by = y - 4
    for tx, ty, tw in taken:  # nudge down while it would sit on top of another caption
        if abs(by - ty) < 9 and bx < tx + tw and tx < bx + w:
            by = ty - 10
    taken.append((bx, by, w))
    drawing.add(Rect(bx, by, w, 10, fillColor=colors.white, strokeColor=None, fillOpacity=0.9))
    drawing.add(String(bx + 3, by + 2.6, text, fontSize=7, fontName="Helvetica", fillColor=INK))


def day_map(
    pins: Sequence[tuple[Point, str, str]],
    path: Sequence[Point],
    color: colors.Color,
    width: float,
    height: float = 210,
    start: tuple[Point, str] | None = None,
    dashed: bool = False,
    basemap: TileBasemap | None = None,
) -> MapView | None:
    """One day: `pins` are (point, number label, name); `start` is yesterday's last stop, drawn hollow.

    `dashed` marks a straight-line estimate (no road geometry) so it is not mistaken for the road itself.
    """
    points = [p for p, _, _ in pins] + ([start[0]] if start else []) + list(path)
    if not points:
        return None
    frame = MercFrame(points, width, height)
    drawing, image = _base(frame, basemap)
    if len(path) > 1:
        _path(drawing, frame, path, color, dashed)
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
    return MapView(drawing, image)


def overview_map(
    days: Sequence[tuple[int, Sequence[Point], Sequence[Point], bool]],
    width: float,
    height: float = 250,
    basemap: TileBasemap | None = None,
) -> MapView | None:
    """Whole trip: per (day index, path, stop points, is estimate) the path in that day's colour, a dot per stop, a "D#" badge."""
    points = [p for _, path, stops, _ in days for p in (*path, *stops)]
    if not points:
        return None
    frame = MercFrame(points, width, height)
    drawing, image = _base(frame, basemap)
    for index, path, _stops, dashed in days:
        if len(path) > 1:
            _path(drawing, frame, path, day_color(index), dashed)
    for index, _path_points, stops, _ in days:
        for point in stops:
            x, y = frame.xy(point)
            drawing.add(Circle(x, y, 3.6, fillColor=colors.white, strokeColor=day_color(index), strokeWidth=1.6))
    for index, _path_points, stops, _ in days:
        if stops:
            x, y = frame.xy(stops[0])
            _pin(drawing, x, y + 11, f"D{index + 1}", day_color(index))
    _decorate(drawing, frame)
    return MapView(drawing, image)
