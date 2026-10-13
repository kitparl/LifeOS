"""Shareable PDF guides for a trip or an adventure.

Written for friends who have never seen LifeOS: plain words, every stat explained, every map point a
tappable Google Maps link. A missing value is never printed as "None" — it always becomes a friendly line
such as "Not decided yet". Pure rendering: callers load the data (see `services/export_service.py`).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date, time
from io import BytesIO
from urllib.parse import urlencode, urlparse
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Flowable,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.modules.travel.export_map import day_color, day_map, overview_map
from app.modules.travel.export_plan import DayPlan, PlannedItem, TripPlan, build_trip_plan
from app.modules.travel.export_tiles import TileBasemap
from app.modules.travel.geo import Point, haversine_m
from app.modules.travel.models import TravelPlace
from app.modules.travel.schemas.adventures import AdventureDetail, AdventureOut
from app.modules.travel.schemas.trips import TripDetail

PRIMARY = colors.HexColor("#0f6b8f")
PRIMARY_SOFT = colors.HexColor("#e6f2f7")
INK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#5f6c7b")
LINE = colors.HexColor("#d3dce4")
LINK = "#0b5cad"
DOT = " \u00b7 "
FOOTER_NAME_MAX = 40

PAGE_W, PAGE_H = A4
MARGIN = 16 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

STATUS_HELP = {
    "draft": "Draft - still an idea. Dates and plans may change.",
    "planning": "Planning - the trip is happening, details are being worked out.",
    "booked": "Booked - tickets / stays are arranged.",
    "active": "On now - the trip is happening right now.",
    "completed": "Completed - the trip is over.",
}
KIND_HELP = {
    "trek": "Trek - a long walk, usually in the mountains, that can take several days.",
    "hike": "Hike - a walk on trails, usually finished in one day.",
    "road_trip": "Road trip - a journey by road with stops on the way.",
    "camping": "Camping - sleeping outdoors in a tent.",
    "cycling": "Cycling - a ride on a bicycle.",
    "expedition": "Expedition - a big, well-planned outdoor journey.",
}
DIFFICULTY_HELP = {
    "easy": "Easy - gentle ground, fine for beginners and kids.",
    "moderate": "Moderate - some steep parts; you should be reasonably fit.",
    "hard": "Hard - long or steep; good fitness and some experience needed.",
    "expert": "Expert - very demanding; only for experienced people with proper gear.",
}
WAYPOINT_HELP = {
    "start": "Start point",
    "camp": "Camp site (sleep here)",
    "summit": "Top of the climb",
    "water": "Drinking water",
    "viewpoint": "Nice view",
    "end": "End point",
    "other": "Stop",
}
MODE_HELP = {
    "driving": "by car",
    "walking": "on foot",
    "cycling": "by bicycle",
    "transit": "by public transport",
}
SOURCE_HELP = {
    "google": "Planned with Google Maps",
    "user_drawn": "Drawn by hand on the map",
    "gpx": "Imported from a GPS track file",
    "straight_line": "Straight lines between stops (not real roads)",
}

# Built-in PDF fonts only cover Latin-1; map common typography first, then drop what cannot be printed.
_TYPOGRAPHY = str.maketrans(
    {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "•": "-", "…": "...", "→": "->", " ": " ", "₹": "Rs "}
)
_WS = re.compile(r"[ \t]+")


def plain(value: object, fallback: str = "") -> str:
    """Printable text; `fallback` when there is nothing to show (so 'None' is never printed)."""
    raw = "" if value is None else str(value)
    raw = raw.translate(_TYPOGRAPHY).encode("latin-1", "ignore").decode("latin-1")
    lines = [_WS.sub(" ", ln).strip() for ln in raw.splitlines()]
    return "\n".join(ln for ln in lines if ln) or fallback


def text(value: object, fallback: str = "") -> str:
    """`plain` text made safe to put inside Paragraph markup."""
    return escape(plain(value, fallback)).replace("\n", "<br/>")


def link(url: str, label: str) -> str:
    return f'<a href="{escape(url, {chr(34): "&quot;"})}" color="{LINK}"><u>{text(label)}</u></a>'


def maps_url(lat: float, lng: float, place_id: str | None = None) -> str:
    params = {"api": "1", "query": f"{lat:.6f},{lng:.6f}"}
    if place_id:
        params["query_place_id"] = place_id
    return f"https://www.google.com/maps/search/?{urlencode(params)}"


MAX_POINTS_PER_LINK = 11  # Google Maps links take an origin, a destination and at most 9 stops in between


def _fmt_point(p: tuple[float, float]) -> str:
    return f"{p[0]:.6f},{p[1]:.6f}"


def route_links(points: Sequence[tuple[float, float]], mode: str) -> list[tuple[str, int, int]]:
    """Google Maps directions links that together cover every point, as (url, first stop no., last stop no.).

    One link holds at most 11 points, so a longer route is split into consecutive parts that share their
    joining point; nothing is dropped. Points repeated back to back are merged first.
    """
    pts = [p for i, p in enumerate(points) if i == 0 or _fmt_point(p) != _fmt_point(points[i - 1])]
    links: list[tuple[str, int, int]] = []
    for start in range(0, max(len(pts) - 1, 0), MAX_POINTS_PER_LINK - 1):
        chunk = pts[start : start + MAX_POINTS_PER_LINK]
        params = {
            "api": "1",
            "origin": _fmt_point(chunk[0]),
            "destination": _fmt_point(chunk[-1]),
            "travelmode": "bicycling" if mode == "cycling" else mode,
        }
        if len(chunk) > 2:
            params["waypoints"] = "|".join(_fmt_point(p) for p in chunk[1:-1])
        links.append((f"https://www.google.com/maps/dir/?{urlencode(params)}", start + 1, start + len(chunk)))
    return links


def route_link_html(points: Sequence[tuple[float, float]], mode: str, label: str) -> str | None:
    """One tappable link, or "Part 1 (stops 1-11) | Part 2 ..." when the route needs several. None if < 2 points."""
    links = route_links(points, mode)
    if not links:
        return None
    if len(links) == 1:
        return link(links[0][0], label)
    parts = DOT.join(link(url, f"Part {i} (stops {first}-{last})") for i, (url, first, last) in enumerate(links, 1))
    return f"{text(label)}: {parts}"


def fmt_date(value: date | None, fallback: str = "Date not decided yet") -> str:
    return value.strftime("%a, %d %b %Y") if value else fallback


def fmt_time(value: time | None) -> str:
    if value is None:
        return "Any time"
    return value.strftime("%I:%M %p").lstrip("0")


def fmt_distance(meters: float | None, fallback: str = "Not planned yet") -> str:
    if not meters:
        return fallback
    km = meters / 1000
    return f"{km:.0f} km" if km >= 100 else f"{km:.1f} km"


def fmt_duration(seconds: int | None, fallback: str = "Not known") -> str:
    if not seconds:
        return fallback
    total = round(seconds / 60)
    hours, minutes = divmod(total, 60)
    return f"{hours} h {minutes} min" if hours else f"{minutes} min"


def fmt_height(meters: float | None, fallback: str = "Not measured") -> str:
    return f"{round(meters)} m" if meters is not None else fallback


# ---- layout pieces ---------------------------------------------------------------------------------


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]
    body = ParagraphStyle("body", parent=base, fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=INK)
    return {
        "body": body,
        "km": ParagraphStyle("km", parent=body, fontSize=8.5, leading=12, textColor=PRIMARY),
        "day_title": ParagraphStyle("day_title", parent=body, fontSize=12.5, leading=16),
        "small": ParagraphStyle("small", parent=body, fontSize=8.5, leading=12, textColor=MUTED),
        "muted": ParagraphStyle("muted", parent=body, textColor=MUTED),
        "title": ParagraphStyle(
            "title", parent=body, fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=colors.white
        ),
        "subtitle": ParagraphStyle("subtitle", parent=body, fontSize=11, leading=15, textColor=colors.white),
        "h1": ParagraphStyle(
            "h1",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=PRIMARY,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "day": ParagraphStyle(
            "day", parent=body, fontName="Helvetica-Bold", fontSize=14, leading=17, textColor=colors.white
        ),
        "tile_value": ParagraphStyle(
            "tile_value",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=PRIMARY,
            alignment=TA_CENTER,
        ),
        "tile_label": ParagraphStyle(
            "tile_label", parent=body, fontSize=8, leading=10, textColor=MUTED, alignment=TA_CENTER
        ),
        "cell_head": ParagraphStyle(
            "cell_head", parent=body, fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=MUTED
        ),
    }


def _outline(flowable: Flowable, label: str, key: str, level: int) -> Flowable:
    """Mark a top-level flowable as a PDF bookmarks-panel entry (see `GuideDoc.afterFlowable`)."""
    flowable.outline = (f"outline-{key}", plain(label, "Section"), level)  # type: ignore[attr-defined]
    return flowable


class Heading(Paragraph):
    """A section heading that is also a bookmark entry and an internal link target."""

    def __init__(self, label: str, style: ParagraphStyle, key: str, level: int = 0):
        super().__init__(f'<a name="{key}"/>{text(label)}', style)
        _outline(self, label, key, level)


class GuideDoc(BaseDocTemplate):
    def __init__(self, buffer: BytesIO, title: str, footer: str):
        super().__init__(
            buffer,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN,
            bottomMargin=18 * mm,
            title=title,
            author="LifeOS",
            subject=footer,
        )
        self.footer = footer
        self.addPageTemplates(
            PageTemplate(
                "main",
                [
                    Frame(
                        MARGIN,
                        18 * mm,
                        CONTENT_W,
                        PAGE_H - MARGIN - 18 * mm,
                        id="body",
                        leftPadding=0,
                        rightPadding=0,
                        topPadding=0,
                        bottomPadding=0,
                    )
                ],
            )
        )

    def afterFlowable(self, flowable: Flowable) -> None:
        outline = getattr(flowable, "outline", None)
        if outline:
            key, title, level = outline
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=level, closed=False)


class _NumberedCanvas(Canvas):
    """Two-pass canvas so each footer can say "Page 2 of 5"."""

    footer = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved: list[dict] = []

    def showPage(self) -> None:
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self.setFont("Helvetica", 8)
            self.setFillColor(MUTED)
            self.setStrokeColor(LINE)
            self.line(MARGIN, 14 * mm, PAGE_W - MARGIN, 14 * mm)
            self.drawString(MARGIN, 9.5 * mm, self.footer)
            self.drawRightString(PAGE_W - MARGIN, 9.5 * mm, f"Page {self._pageNumber} of {total}")
            super().showPage()
        super().save()


def _build(title: str, footer: str, story: list[Flowable]) -> bytes:
    buffer = BytesIO()
    canvas_cls = type("FooterCanvas", (_NumberedCanvas,), {"footer": footer})
    GuideDoc(buffer, title, footer).build(story, canvasmaker=canvas_cls)
    return buffer.getvalue()


def _banner(title: str, lines: list[str], st: dict[str, ParagraphStyle]) -> Table:
    cells = [[Paragraph(text(title, "Untitled"), st["title"])]]
    cells += [[Paragraph(text(ln), st["subtitle"])] for ln in lines if ln]
    table = Table(cells, colWidths=[CONTENT_W])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (0, 0), 16),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 16),
                ("TOPPADDING", (0, 1), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -2), 2),
            ]
        )
    )
    return table


def _tiles(items: list[tuple[str, str]], st: dict[str, ParagraphStyle]) -> Table:
    width = CONTENT_W / len(items)
    table = Table(
        [
            [Paragraph(text(v), st["tile_value"]) for v, _ in items],
            [Paragraph(text(lb), st["tile_label"]) for _, lb in items],
        ],
        colWidths=[width] * len(items),
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PRIMARY_SOFT),
                ("LINEAFTER", (0, 0), (-2, -1), 0.6, colors.white),
                ("TOPPADDING", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
                ("TOPPADDING", (0, 1), (-1, 1), 0),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ]
        )
    )
    return table


def _grid(
    rows: list[list[Paragraph | str]], widths: list[float], st: dict[str, ParagraphStyle], head: list[str]
) -> Table:
    data = [[Paragraph(text(h), st["cell_head"]) for h in head]] + [
        [c if isinstance(c, Paragraph) else Paragraph(c, st["body"]) for c in row] for row in rows
    ]
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_SOFT),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _tip_box(lines: list[str], st: dict[str, ParagraphStyle]) -> Table:
    table = Table([[Paragraph("<br/>".join(lines), st["body"])]], colWidths=[CONTENT_W])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, PRIMARY),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7fbfd")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _notes_block(label: str, value: str | None, empty: str, st: dict[str, ParagraphStyle]) -> list[Flowable]:
    return [Paragraph(text(label), st["h1"]), Paragraph(text(value, empty), st["body"])]


def _links_line(urls: Sequence[str]) -> str:
    return " &nbsp; ".join(link(u, f"Link {i}" if len(urls) > 1 else "Open link") for i, u in enumerate(urls, 1))


# ---- trip -------------------------------------------------------------------------------------------

STATUS_SHORT = {
    "draft": "Draft - plans may still change",
    "planning": "Planning",
    "booked": "Booked",
    "active": "Happening now",
    "completed": "Completed",
}
DOT = " · "


def _trip_length(detail: TripDetail) -> int:
    trip = detail.trip
    if trip.start_date and trip.end_date:
        return (trip.end_date - trip.start_date).days + 1
    return len(detail.days)


def _km(meters: float, approx: bool) -> str:
    return ("~" if approx else "") + fmt_distance(meters)


def _site(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host or "Open link"


def _day_title(plan: DayPlan) -> str:
    if plan.day.title:
        return plan.day.title
    names = [i.place.name for i in plan.items if i.place]
    if not names:
        return "Free day" if not plan.items else "Day plan"
    return names[0] if len(set(names)) == 1 else f"{names[0]} to {names[-1]}"


def _day_path(plan: DayPlan) -> list[Point]:
    path: list[Point] = []
    for leg in plan.legs:
        path.extend(leg.path)
    return path


def _badge(number: int, color: colors.Color) -> Drawing:
    badge = Drawing(20, 20)
    badge.add(Circle(10, 10, 8.5, fillColor=color, strokeColor=None))
    badge.add(
        String(
            10, 7.2, str(number), fontSize=8.5, fontName="Helvetica-Bold", textAnchor="middle", fillColor=colors.white
        )
    )
    return badge


def _stop_cell(stop: PlannedItem, st: dict[str, ParagraphStyle]) -> list[Flowable]:
    item, place = stop.item, stop.place
    clock = ""
    if item.start_time:
        clock = fmt_time(item.start_time) + (f" to {fmt_time(item.end_time)}" if item.end_time else "")
    cell: list[Flowable] = [Paragraph(f"<b>{text(item.title, 'Stop')}</b>", st["body"])]
    if clock:
        cell.append(Paragraph(text(clock), st["small"]))
    if stop.leg:
        leg = stop.leg
        how = f"{_km(leg.meters, leg.approx)} from {text(leg.from_name)}"
        if leg.seconds:
            how += f", about {fmt_duration(leg.seconds)}"
        elif leg.approx:
            how += " in a straight line (the road will be longer)"
        cell.append(Paragraph(how, st["km"]))
    if place is not None:
        where = ", ".join(p for p in (place.address or place.city, place.region, place.country) if p)
        if where and plain(where) != plain(item.title):
            cell.append(Paragraph(text(where), st["small"]))
    for label, value in (("Getting there", item.transport), ("Stay", item.accommodation)):
        if value:
            cell.append(Paragraph(f"<b>{label}:</b> {text(value)}", st["body"]))
    if item.notes:
        cell.append(Paragraph(text(item.notes), st["body"]))
    links = []
    if place is not None:
        links.append(link(maps_url(place.lat, place.lng, place.external_place_id), "Open in Maps"))
    links += [link(u, _site(u)) for u in item.links]
    if links:
        cell.append(Paragraph(" &nbsp;&nbsp; ".join(links), st["small"]))
    return cell


def _day_summary(plan: DayPlan) -> str:
    parts = []
    if plan.legs:
        parts.append(
            f"<b>{_km(plan.meters, plan.approx)}</b>" + (" by road" if not plan.approx else " (straight line)")
        )
        if plan.seconds:
            parts.append(f"about {fmt_duration(plan.seconds)} on the road")
    placed = sum(1 for i in plan.items if i.place)
    if placed:
        parts.append(f"{placed} {'stop' if placed == 1 else 'stops'}")
    if plan.stay:
        parts.append("Sleep at " + ", ".join(text(s) for s in plan.stay))
    return DOT.join(parts)


def _day_flowables(
    plan: DayPlan, mode: str, st: dict[str, ParagraphStyle], basemap: TileBasemap | None
) -> list[Flowable]:
    day = plan.day
    n = day.day_index + 1
    color = day_color(day.day_index)
    key = f"day{n}"
    when = fmt_date(day.day_date, "Date not set")
    head = Table(
        [
            [
                Paragraph(f'<a name="{key}"/>DAY {n}', st["day"]),
                [Paragraph(text(when), st["small"]), Paragraph(f"<b>{text(_day_title(plan))}</b>", st["day_title"])],
            ]
        ],
        colWidths=[26 * mm, CONTENT_W - 26 * mm],
    )
    head.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), color),
                ("BACKGROUND", (1, 0), (1, 0), PRIMARY_SOFT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    _outline(head, f"Day {n}: {_day_title(plan)}", key, 1)
    top: list[Flowable] = [CondPageBreak(95 * mm), head]
    summary = _day_summary(plan)
    if summary:
        top += [Spacer(1, 4), Paragraph(summary, st["body"])]
    if day.notes:
        top += [Spacer(1, 3), Paragraph(text(day.notes), st["body"])]

    pins: dict[str, tuple[Point, list[str], str]] = {}
    for stop in plan.items:
        if stop.place:
            point, numbers, _ = pins.setdefault(stop.place.id, ((stop.place.lat, stop.place.lng), [], stop.place.name))
            numbers.append(str(stop.number))
    previous = (plan.previous, plan.previous_name or "yesterday") if plan.previous and plan.legs else None
    chart = day_map(
        [(pt, ",".join(nums), name) for pt, nums, name in pins.values()],
        _day_path(plan),
        color,
        CONTENT_W,
        start=previous,
        dashed=plan.approx,
        basemap=basemap,
    )
    if chart is not None:
        top += [Spacer(1, 6), chart]
        html = route_link_html(plan.points, mode, "Open this day's route in Google Maps")
        if html is None:
            only = next(i.place for i in plan.items if i.place)
            html = link(maps_url(only.lat, only.lng, only.external_place_id), "Open this place in Google Maps")
        top.append(Paragraph(html, st["small"]))
        if plan.approx:
            top.append(
                Paragraph("Distances for this day are straight-line estimates; the road will be longer.", st["small"])
            )
    if not plan.items:
        return top + [Spacer(1, 3), Paragraph("Nothing planned yet. A free day to rest or explore.", st["muted"])]

    rows = [[_badge(s.number, color), _stop_cell(s, st)] for s in plan.items]
    table = Table(rows, colWidths=[12 * mm, CONTENT_W - 12 * mm], splitByRow=1)
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
                ("LEFTPADDING", (0, 0), (0, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return top + [Spacer(1, 6), table, Spacer(1, 14)]


def _is_blank(plan: DayPlan) -> bool:
    return not plan.items and not plan.day.notes and not plan.day.title


def _runs(days: Sequence[DayPlan]) -> list[list[DayPlan]]:
    """Consecutive empty days travel together so a half-planned trip does not print ten blank days."""
    runs: list[list[DayPlan]] = []
    for d in days:
        if runs and _is_blank(d) and _is_blank(runs[-1][0]):
            runs[-1].append(d)
        else:
            runs.append([d])
    return runs


def _span(run: Sequence[DayPlan]) -> tuple[str, str]:
    first, last = run[0].day, run[-1].day
    number = f"{first.day_index + 1}" if len(run) == 1 else f"{first.day_index + 1}-{last.day_index + 1}"
    short = "%a %d %b"
    if not first.day_date:
        return number, "Date not set"
    when = first.day_date.strftime(short)
    return number, when if len(run) == 1 else f"{when} to {last.day_date.strftime(short) if last.day_date else '...'}"


def _glance(plan: TripPlan, st: dict[str, ParagraphStyle]) -> Table:
    rows = []
    for run in _runs(plan.days):
        d = run[0]
        number, when = _span(run)
        if _is_blank(d):
            title, distance = "Nothing planned yet", "No travel"
        else:
            title = f'<a href="#day{d.day.day_index + 1}" color="{LINK}">{text(_day_title(d))}</a>'
            distance = _km(d.meters, d.approx) if d.legs else "No travel"
        rows.append(
            [
                Paragraph(f"<b>{number}</b>", st["body"]),
                Paragraph(text(when), st["body"]),
                Paragraph(title, st["body"]),
                Paragraph(distance, st["body"]),
                Paragraph(text(", ".join(d.stay), "Not decided yet"), st["body"]),
            ]
        )
    return _grid(
        rows,
        [16 * mm, 42 * mm, CONTENT_W - 16 * mm - 42 * mm - 24 * mm - 38 * mm, 24 * mm, 38 * mm],
        st,
        ["Day", "Date", "Plan", "Distance", "Where we sleep"],
    )


def _unscheduled(
    detail: TripDetail, places: dict[str, TravelPlace], plan: TripPlan, st: dict[str, ParagraphStyle]
) -> list[Flowable]:
    used = {i.place.id for d in plan.days for i in d.items if i.place}
    rest = [p for p in detail.places if p.id not in used]
    if not rest:
        return []
    rows = []
    for p in rest:
        full = places.get(p.id)
        where = ", ".join(x for x in ((full.city, full.region, full.country) if full else ()) if x)
        rows.append(
            [
                Paragraph(f"<b>{text(p.name)}</b>", st["body"]),
                Paragraph(text(where, "Location not named"), st["body"]),
                Paragraph(link(maps_url(p.lat, p.lng, p.external_place_id), "Map"), st["body"]),
            ]
        )
    return [
        Heading("Also on the list, not on a day yet", st["h1"], "unscheduled"),
        _grid(rows, [60 * mm, CONTENT_W - 60 * mm - 20 * mm, 20 * mm], st, ["Place", "Where", "Open"]),
    ]


def _adventures_section(adventures: Sequence[AdventureOut], st: dict[str, ParagraphStyle]) -> list[Flowable]:
    if not adventures:
        return []
    rows = []
    for a in adventures:
        when = fmt_date(a.start_date, "Dates not set") + (f" to {fmt_date(a.end_date)}" if a.end_date else "")
        rows.append(
            [
                Paragraph(f"<b>{text(a.name)}</b>", st["body"]),
                Paragraph(text(KIND_HELP.get(a.kind), a.kind.replace("_", " ").title()), st["body"]),
                Paragraph(text(DIFFICULTY_HELP.get(a.difficulty or ""), "Difficulty not rated yet"), st["body"]),
                Paragraph(text(when), st["body"]),
            ]
        )
    return [
        Heading("Adventures on this trip", st["h1"], "adventures"),
        _grid(
            rows, [36 * mm, 50 * mm, 50 * mm, CONTENT_W - 136 * mm], st, ["Adventure", "What it is", "How hard", "When"]
        ),
    ]


def trip_guide_pdf(
    detail: TripDetail,
    places: dict[str, TravelPlace],
    adventures: Sequence[AdventureOut],
    basemap: TileBasemap | None = None,
    share_url: str | None = None,
) -> bytes:
    """`share_url`: the trip's active share link, printed in every page footer (requirements D-05)."""
    st = _styles()
    trip = detail.trip
    plan = build_trip_plan(detail, places)
    length = _trip_length(detail)
    route = detail.route
    mode = route.mode if route else "driving"

    dates = f"{fmt_date(trip.start_date)} to {fmt_date(trip.end_date)}" if trip.start_date else "Dates not decided yet"
    if length and trip.start_date:
        dates += f"{DOT}{length} {'day' if length == 1 else 'days'}"
    status = STATUS_SHORT.get(trip.status, trip.status.title())
    if trip.dates_tentative and trip.start_date:
        status += ", dates may change"
    story: list[Flowable] = [
        _banner(trip.name, [dates, status], st),
        Spacer(1, 10),
        _tiles(
            [
                (str(length) if length else "Not set", "Days"),
                (_km(plan.meters, plan.approx) if plan.meters else "Not planned", "Total distance"),
                (fmt_duration(plan.seconds, "Not known"), "Time on the road"),
                (str(len(detail.places)), "Places"),
            ],
            st,
        ),
    ]
    if trip.description:
        story += [Spacer(1, 8), Paragraph(text(trip.description), st["body"])]

    overview = overview_map(
        [
            (d.day.day_index, _day_path(d), [(i.place.lat, i.place.lng) for i in d.items if i.place], d.approx)
            for d in plan.days
        ],
        CONTENT_W,
        basemap=basemap,
    )
    if overview is not None:
        story += [Heading("The whole route", st["h1"], "route"), overview]
        html = route_link_html(
            [(s.lat, s.lng) for s in detail.stops], mode, "Open every stop of the trip in Google Maps"
        )
        note = "Tap any underlined text to open it in Google Maps."
        if plan.approx:
            note += " Distances marked ~ are straight-line estimates; real roads are longer."
        story.append(Paragraph((html + DOT if html else "") + text(note), st["small"]))
    if plan.days:
        story += [Heading("Day by day at a glance", st["h1"], "glance"), _glance(plan, st)]
        for run in _runs(plan.days):
            if _is_blank(run[0]):
                number, when = _span(run)
                story.append(
                    Paragraph(
                        f"<b>{'Day' if len(run) == 1 else 'Days'} {number}</b> ({text(when)}): nothing planned yet.",
                        st["muted"],
                    )
                )
            else:
                story += _day_flowables(run[0], mode, st, basemap)
    story += _unscheduled(detail, places, plan, st)
    story += _adventures_section(adventures, st)
    if trip.notes:
        story += [Heading("Good to know", st["h1"], "notes"), Paragraph(text(trip.notes), st["body"])]
    return _build(f"{plain(trip.name)} - trip guide", _trip_footer(plain(trip.name), share_url), story)


def _trip_footer(name: str, share_url: str | None) -> str:
    if not share_url:
        return f"{name} - shared from LifeOS"
    # The page number shares the footer line, so a long name is shortened to keep the link whole.
    short = name if len(name) <= FOOTER_NAME_MAX else name[: FOOTER_NAME_MAX - 3] + "..."
    return f"{short} - plan it with us: {share_url}"


# ---- adventure --------------------------------------------------------------------------------------


def _elevation_chart(profile: Sequence[float]) -> Drawing:
    width, height, pad = CONTENT_W, 110, 28
    drawing = Drawing(width, height)
    low, high = min(profile), max(profile)
    span = (high - low) or 1
    step = (width - pad - 8) / max(len(profile) - 1, 1)
    coords: list[float] = []
    for i, value in enumerate(profile):
        coords += [pad + i * step, 18 + (value - low) / span * (height - 34)]
    drawing.add(Line(pad, 18, width - 8, 18, strokeColor=LINE))
    drawing.add(PolyLine(coords, strokeColor=PRIMARY, strokeWidth=1.6))
    drawing.add(String(0, height - 12, f"{round(high)} m", fontSize=7, fillColor=MUTED))
    drawing.add(String(0, 14, f"{round(low)} m", fontSize=7, fillColor=MUTED))
    drawing.add(String(pad, 4, "Start", fontSize=7, fillColor=MUTED))
    drawing.add(String(width - 28, 4, "End", fontSize=7, fillColor=MUTED))
    return drawing


def adventure_guide_pdf(detail: AdventureDetail, trip_name: str | None, basemap: TileBasemap | None = None) -> bytes:
    st = _styles()
    adv, route = detail.adventure, detail.route
    when = (
        f"{fmt_date(adv.start_date)}  to  {fmt_date(adv.end_date)}"
        if adv.start_date and adv.end_date
        else fmt_date(adv.start_date, "Dates not decided yet")
    )
    subtitle = [when, KIND_HELP.get(adv.kind, adv.kind.replace("_", " ").title())]
    if trip_name:
        subtitle.append(f"Part of the trip: {trip_name}")
    story: list[Flowable] = [
        _banner(adv.name, subtitle, st),
        Spacer(1, 10),
        _tiles(
            [
                (adv.difficulty.title() if adv.difficulty else "Not rated", "Difficulty"),
                (fmt_distance(route.distance_m if route else None, "Not planned"), "Distance"),
                (fmt_height(route.elevation_gain_m if route else None, "Not measured"), "Total climb up"),
                (fmt_height(route.elevation_loss_m if route else None, "Not measured"), "Total way down"),
            ],
            st,
        ),
        Spacer(1, 10),
        _tip_box(
            [
                "<b>What this means</b>",
                text(DIFFICULTY_HELP.get(adv.difficulty or ""), "Difficulty has not been rated yet."),
                "Climb up / way down add up all the uphill and downhill parts of the walk.",
                "Blue underlined words open the place in Google Maps.",
            ],
            st,
        ),
        *_notes_block("About this adventure", adv.notes, "No notes have been written yet.", st),
    ]
    story.append(Heading("Route", st["h1"], "route"))
    if route is None:
        story.append(Paragraph("No route has been drawn or imported yet.", st["muted"]))
    else:
        story.append(
            Paragraph(
                f"{text(route.name, 'Route')}: <b>{fmt_distance(route.distance_m)}</b>. "
                f"{text(SOURCE_HELP.get(route.source), 'Planned in LifeOS')}.",
                st["body"],
            )
        )
        trail = [(w.lat, w.lng) for w in sorted(detail.waypoints, key=lambda w: w.position)] or [
            tuple(p) for p in detail.route_points[:: max(len(detail.route_points) // 10, 1)]
        ]
        html = route_link_html(trail, route.mode, "Open the route in Google Maps")
        if html:
            story += [Spacer(1, 4), Paragraph(html, st["body"])]
    story.append(Heading("Height along the way", st["h1"], "elevation"))
    if detail.elevation_profile and len(detail.elevation_profile) >= 2:
        story += [
            _elevation_chart(detail.elevation_profile),
            Paragraph("Higher on the chart means higher above sea level.", st["small"]),
        ]
    else:
        story.append(Paragraph("Height details are not available for this route yet.", st["muted"]))
    story.append(Heading("Important stops", st["h1"], "stops"))
    waypoints = sorted(detail.waypoints, key=lambda w: w.position)
    if waypoints:
        spots = [(w.lat, w.lng) for w in waypoints]
        along = [0.0]
        for a, b in zip(spots, spots[1:], strict=False):
            along.append(along[-1] + haversine_m(a, b))
        chart = day_map(
            [(pt, str(i), w.name) for i, (pt, w) in enumerate(zip(spots, waypoints, strict=True), 1)],
            [tuple(p) for p in detail.route_points] or spots,
            day_color(0),
            CONTENT_W,
            basemap=basemap,
        )
        if chart is not None:
            story += [chart, Spacer(1, 6)]
        rows = [
            [
                Paragraph(f"<b>{i}. {text(w.name, 'Stop')}</b>", st["body"]),
                Paragraph(text(WAYPOINT_HELP.get(w.kind), "Stop"), st["body"]),
                Paragraph(fmt_height(w.elevation_m, "Height not known"), st["body"]),
                Paragraph("Start" if i == 1 else f"~{fmt_distance(along[i - 1])}", st["body"]),
                Paragraph(link(maps_url(w.lat, w.lng), "Map"), st["body"]),
            ]
            for i, w in enumerate(waypoints, 1)
        ]
        story.append(
            _grid(
                rows,
                [52 * mm, 42 * mm, 32 * mm, 32 * mm, CONTENT_W - 158 * mm],
                st,
                ["Stop", "What it is", "Height above sea", "From the start", "Open"],
            )
        )
        story.append(
            Paragraph("~ means a straight-line estimate between stops; the trail itself is longer.", st["small"])
        )
    else:
        story.append(Paragraph("No stops have been marked on this adventure yet.", st["muted"]))
    return _build(f"{plain(adv.name)} - adventure guide", f"{plain(adv.name)} - shared from LifeOS", story)
