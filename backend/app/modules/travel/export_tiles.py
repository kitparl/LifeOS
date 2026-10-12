"""Web-mercator view maths and a polite map-tile fetcher for the PDF guides.

Tiles are optional decoration: any failure (offline server, blocked host, slow response) makes
`TileBasemap.render` return None and the guide falls back to the plain schematic map.
"""

from __future__ import annotations

import math
from collections import OrderedDict
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import httpx
from PIL import Image
from reportlab.lib.utils import ImageReader

from app.core.config import get_settings
from app.modules.travel.geo import Point

TILE_PX = 256
MAX_ZOOM = 16
MAX_TILES_PER_MAP = 30
TILE_BUDGET_PER_GUIDE = 160
CACHE_TILES = 400
FETCH_TIMEOUT_S = 5.0
FETCH_WORKERS = 8
PAD = 22
EQUATOR_M_PER_PX_Z0 = 156_543.03392
USER_AGENT = "LifeOS-travel-guide/1.0 (personal trip planner PDF export)"

TileFetcher = Callable[[int, int, int], bytes | None]


def _world(point: Point) -> tuple[float, float]:
    """Lat/lng to world pixels on a 256 px (zoom 0) mercator world, y growing southwards."""
    lat = max(min(point[0], 85.0511), -85.0511)
    x = (point[1] + 180.0) / 360.0 * TILE_PX
    y = (0.5 - math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) / (2 * math.pi)) * TILE_PX
    return x, y


class MercFrame:
    """Fits points into a width x height drawing (points) so every map overlay shares one projection."""

    def __init__(self, points: Sequence[Point], width: float, height: float):
        world = [_world(p) for p in points]
        xs, ys = [w[0] for w in world], [w[1] for w in world]
        min_extent = TILE_PX / 2**MAX_ZOOM * 40  # a single point still gets a street-level view
        span_x = max(max(xs) - min(xs), min_extent)
        span_y = max(max(ys) - min(ys), min_extent)
        self.width, self.height = width, height
        self.zoom_f = min(math.log2(min((width - 2 * PAD) / span_x, (height - 2 * PAD) / span_y)), MAX_ZOOM)
        self.k = 2**self.zoom_f  # drawing points per zoom-0 world pixel
        self.cx = (min(xs) + max(xs)) / 2
        self.cy = (min(ys) + max(ys)) / 2
        mid_lat = sum(p[0] for p in points) / len(points)
        self.km_per_pt = EQUATOR_M_PER_PX_Z0 * math.cos(math.radians(mid_lat)) / self.k / 1000

    def xy(self, point: Point) -> tuple[float, float]:
        wx, wy = _world(point)
        return self.width / 2 + (wx - self.cx) * self.k, self.height / 2 - (wy - self.cy) * self.k


def _http_fetcher(url_template: str) -> TileFetcher:
    client = httpx.Client(timeout=FETCH_TIMEOUT_S, headers={"User-Agent": USER_AGENT}, follow_redirects=True)

    def fetch(z: int, x: int, y: int) -> bytes | None:
        try:
            resp = client.get(url_template.format(z=z, x=x, y=y))
        except httpx.HTTPError:
            return None
        return resp.content if resp.status_code == 200 and resp.content else None

    return fetch


class TileBasemap:
    """Stitches map tiles into one image per drawing. Holds a small cache and a per-guide request budget."""

    def __init__(self, fetch: TileFetcher, attribution: str = ""):
        self._fetch = fetch
        self.attribution = attribution
        self._cache: OrderedDict[tuple[int, int, int], bytes] = OrderedDict()
        self._budget = TILE_BUDGET_PER_GUIDE

    @classmethod
    def from_settings(cls) -> TileBasemap | None:
        settings = get_settings()
        if not settings.travel_map_tiles or not settings.travel_map_tile_url:
            return None
        return cls(_http_fetcher(settings.travel_map_tile_url), settings.travel_map_attribution)

    def render(self, frame: MercFrame) -> ImageReader | None:
        z = min(math.ceil(frame.zoom_f), MAX_ZOOM)
        scale = 2 ** (frame.zoom_f - z)  # drawing points per tile pixel
        half_w, half_h = frame.width / 2 / scale, frame.height / 2 / scale
        cx, cy = frame.cx * 2**z, frame.cy * 2**z
        limit = 2**z
        x0, x1 = math.floor((cx - half_w) / TILE_PX), math.floor((cx + half_w) / TILE_PX)
        y0, y1 = max(math.floor((cy - half_h) / TILE_PX), 0), min(math.floor((cy + half_h) / TILE_PX), limit - 1)
        wanted = [(z, x % limit, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
        missing = [t for t in dict.fromkeys(wanted) if t not in self._cache]
        if not wanted or len(wanted) > MAX_TILES_PER_MAP or len(missing) > self._budget:
            return None
        if missing:
            self._budget -= len(missing)
            with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
                for tile, data in zip(missing, pool.map(lambda t: self._fetch(*t), missing), strict=True):
                    if data:
                        self._remember(tile, data)
        if any(t not in self._cache for t in wanted):
            return None
        return self._compose(frame, z, scale, (x0, y0, x1, y1), (cx - half_w, cy - half_h, cx + half_w, cy + half_h))

    def _remember(self, tile: tuple[int, int, int], data: bytes) -> None:
        self._cache[tile] = data
        while len(self._cache) > CACHE_TILES:
            self._cache.popitem(last=False)

    def _compose(self, frame, z, scale, tiles, view) -> ImageReader | None:
        x0, y0, x1, y1 = tiles
        limit = 2**z
        sheet = Image.new("RGB", ((x1 - x0 + 1) * TILE_PX, (y1 - y0 + 1) * TILE_PX), "white")
        try:
            for x in range(x0, x1 + 1):
                for y in range(y0, y1 + 1):
                    tile = Image.open(BytesIO(self._cache[(z, x % limit, y)])).convert("RGB")
                    sheet.paste(tile, ((x - x0) * TILE_PX, (y - y0) * TILE_PX))
        except OSError:  # a corrupt tile: show the schematic map instead
            return None
        left, top = view[0] - x0 * TILE_PX, view[1] - y0 * TILE_PX
        box = (round(left), round(top), round(left + frame.width / scale), round(top + frame.height / scale))
        out = sheet.crop(box).resize((round(frame.width * 2), round(frame.height * 2)), Image.LANCZOS)
        return ImageReader(Image.blend(out, Image.new("RGB", out.size, "white"), 0.14))  # soften so overlays stand out
