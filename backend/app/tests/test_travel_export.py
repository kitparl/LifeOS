"""Travel OS — shareable PDF guides for trips and adventures."""

from __future__ import annotations

import io

import pytest
from app.modules.travel.export_pdf import fmt_distance, fmt_duration, plain, route_link_html, route_links, text
from app.modules.travel.export_tiles import TileBasemap
from app.modules.travel.services import export_service
from app.modules.travel.services.export_service import file_name
from app.tests.test_travel_trips import _dated_itinerary, _himachal
from app.tests.travel_support import auth as _auth
from app.tests.travel_support import connect_google as _connect_google

BASE = "/api/v1/travel"
pytestmark = pytest.mark.usefixtures("isolated_uploads")


@pytest.fixture(autouse=True)
def _no_network_tiles(monkeypatch):
    """Guides must render without the network; tests that want tiles inject a fake fetcher."""
    monkeypatch.setattr(export_service.TileBasemap, "from_settings", classmethod(lambda cls: None))


def _fake_tile(z: int, x: int, y: int) -> bytes:
    from io import BytesIO

    from PIL import Image

    out = BytesIO()
    Image.new("RGB", (256, 256), (200 + (x * 7) % 40, 220, 190 + (y * 5) % 40)).save(out, "PNG")
    return out.getvalue()


def _images(content: bytes) -> int:
    pypdf = pytest.importorskip("pypdf")
    return sum(len(page.images) for page in pypdf.PdfReader(io.BytesIO(content)).pages)


def _pdf_text(content: bytes) -> str:
    pypdf = pytest.importorskip("pypdf")
    return "\n".join(page.extract_text() for page in pypdf.PdfReader(io.BytesIO(content)).pages)


def test_missing_values_become_friendly_words_never_none():
    assert plain(None, "Not decided yet") == "Not decided yet"
    assert plain("   ", "Not decided yet") == "Not decided yet"
    assert fmt_distance(None) == "Not planned yet" and fmt_duration(None) == "Not known"
    assert "None" not in text(None) and text("a < b & c") == "a &lt; b &amp; c"


def test_unprintable_characters_are_dropped_not_boxed():
    assert plain("Trek – “Mana” \U0001f3d4️") == 'Trek - "Mana"'
    assert file_name("Himachal 2027 ✨", "trip") == "Himachal-2027-guide.pdf"
    assert file_name("✨", "trip") == "trip-guide.pdf"


def test_route_links_cover_every_stop_in_connected_parts():
    assert route_links([(1.0, 2.0)], "driving") == [] and route_link_html([(1.0, 2.0)], "driving", "Go") is None
    points = [(float(i), 0.5) for i in range(25)]
    links = route_links(points, "cycling")
    assert [(first, last) for _, first, last in links] == [(1, 11), (11, 21), (21, 25)]  # parts share a joining stop
    assert all("travelmode=bicycling" in url for url, _, _ in links)
    assert all(url.count("%7C") <= 8 for url, _, _ in links)  # at most 9 stops between origin and destination
    seen = {f"{p[0]:.6f}%2C{p[1]:.6f}" for p in points}
    joined = " ".join(url for url, _, _ in links)
    assert all(coord in joined for coord in seen)
    assert route_links([(1.0, 2.0), (1.0, 2.0), (3.0, 4.0)], "driving")[0][2] == 2  # back-to-back repeats merge
    assert "Part 3 (stops 21-25)" in route_link_html(points, "driving", "Open all")


@pytest.mark.asyncio
async def test_trip_pdf_is_a_complete_guide(client):
    h = await _auth(client, "pdftrip@example.com")
    places, tid = await _himachal(client, h)
    await _dated_itinerary(client, h, places, tid)
    resp = await client.get(f"{BASE}/trips/{tid}/export", headers=h)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.headers["content-disposition"] == 'attachment; filename="Himachal-2027-guide.pdf"'
    assert resp.content.startswith(b"%PDF")
    content = _pdf_text(resp.content)
    for expected in ("Himachal 2027", "DAY 1", "Manali", "Hampta Pass", "Chandratal", "Open in Maps"):
        assert expected in content
    assert "km" in content and "straight line" in content  # no Google key: estimates, clearly labelled
    assert "Days 3-10" in content and content.count("DAY ") == 2  # empty days are folded into one line
    assert "None" not in content and "null" not in content and "undefined" not in content


@pytest.mark.asyncio
async def test_empty_draft_trip_still_exports_without_blanks(client):
    h = await _auth(client, "pdfdraft@example.com")
    _, tid = await _himachal(client, h)
    resp = await client.get(f"{BASE}/trips/{tid}/export", headers=h)
    assert resp.status_code == 200
    content = _pdf_text(resp.content)
    assert "Dates not decided yet" in content and "Nothing planned yet" not in content
    assert "None" not in content and "null" not in content


@pytest.mark.asyncio
async def test_adventure_pdf_and_ownership(client):
    h = await _auth(client, "pdfadv@example.com")
    created = await client.post(f"{BASE}/adventures", json={"name": "Hampta Pass trek", "kind": "trek"}, headers=h)
    aid = created.json()["adventure"]["id"]
    resp = await client.get(f"{BASE}/adventures/{aid}/export", headers=h)
    assert resp.status_code == 200 and resp.content.startswith(b"%PDF")
    content = _pdf_text(resp.content)
    assert "Hampta Pass trek" in content and "Difficulty has not been rated yet" in content
    assert "None" not in content and "null" not in content

    other = await _auth(client, "pdfother@example.com")
    assert (await client.get(f"{BASE}/adventures/{aid}/export", headers=other)).status_code == 404
    assert (await client.get(f"{BASE}/trips/{aid}/export", headers=other)).status_code == 404


@pytest.mark.asyncio
async def test_trip_pdf_uses_road_legs_when_the_route_is_current(client, google):
    h = await _auth(client, "pdfroad@example.com")
    await _connect_google(client, h)
    places, tid = await _himachal(client, h)
    await _dated_itinerary(client, h, places, tid)
    await client.post(f"{BASE}/trips/{tid}/route", json={"mode": "driving"}, headers=h)
    content = _pdf_text((await client.get(f"{BASE}/trips/{tid}/export", headers=h)).content)
    assert "50.0 km from Manali, about 50 min" in content  # leg 1 of the fake Google route
    assert "73.5 km from Hampta Pass, about 1 h 10 min" in content
    assert "by road" in content and "straight-line estimates" not in content


@pytest.mark.asyncio
async def test_maps_use_real_tiles_and_fall_back_without_them(client, monkeypatch):
    h = await _auth(client, "pdftiles@example.com")
    places, tid = await _himachal(client, h)
    await _dated_itinerary(client, h, places, tid)
    url = f"{BASE}/trips/{tid}/export"

    plain_map = await client.get(url, headers=h)
    assert plain_map.status_code == 200 and _images(plain_map.content) == 0

    fake = lambda cls: TileBasemap(_fake_tile, "(c) Test map data")  # noqa: E731
    monkeypatch.setattr(export_service.TileBasemap, "from_settings", classmethod(fake))
    tiled = await client.get(url, headers=h)
    assert tiled.status_code == 200 and _images(tiled.content) == 3  # overview + one per planned day
    assert "Test map data" in _pdf_text(tiled.content)

    offline = lambda cls: TileBasemap(lambda z, x, y: None)  # noqa: E731
    monkeypatch.setattr(export_service.TileBasemap, "from_settings", classmethod(offline))
    fallback = await client.get(url, headers=h)
    assert fallback.status_code == 200 and _images(fallback.content) == 0  # blocked tiles never break the PDF


def test_tile_image_and_pins_share_one_projection():
    """A black dot is painted on the tile at a known place; the pin for that place must land on it."""
    import math
    from io import BytesIO

    from app.modules.travel.export_tiles import TILE_PX, MercFrame, _world
    from PIL import Image

    target = (32.2432, 77.1892)
    frame = MercFrame([target, (32.30, 77.30)], 500, 200)
    z = min(math.ceil(frame.zoom_f), 16)
    wx, wy = (c * 2**z for c in _world(target))
    tile_x, tile_y = int(wx // TILE_PX), int(wy // TILE_PX)

    def fetch(zoom: int, x: int, y: int) -> bytes:
        tile = Image.new("RGB", (TILE_PX, TILE_PX), "white")
        if (x, y) == (tile_x, tile_y):
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    tile.putpixel((int(wx % TILE_PX) + dx, int(wy % TILE_PX) + dy), (0, 0, 0))
        out = BytesIO()
        tile.save(out, "PNG")
        return out.getvalue()

    image = TileBasemap(fetch).render(frame)._image
    x, y = frame.xy(target)
    px, py = round(x * 2), round((frame.height - y) * 2)  # image is 2 px per point, origin top-left
    assert sum(image.getpixel((px, py))) < 300  # dark: the pin sits on the painted spot
    assert sum(image.getpixel((px + 40, py))) > 600  # and the area around it is the plain tile
