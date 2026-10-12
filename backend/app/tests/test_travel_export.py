"""Travel OS — shareable PDF guides for trips and adventures."""

from __future__ import annotations

import io

import pytest
from app.modules.travel.export_pdf import directions_url, fmt_distance, fmt_duration, plain, text
from app.modules.travel.services.export_service import file_name
from app.tests.test_travel_trips import _dated_itinerary, _himachal
from app.tests.travel_support import auth as _auth

BASE = "/api/v1/travel"
pytestmark = pytest.mark.usefixtures("isolated_uploads")


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


def test_directions_need_two_points_and_cap_waypoints():
    assert directions_url([(1.0, 2.0)], "driving") is None
    url = directions_url([(float(i), 0.0) for i in range(20)], "cycling")
    assert url is not None and "travelmode=bicycling" in url and url.count("%7C") == 8


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
    for expected in ("Himachal 2027", "Day 1", "Manali", "Hampta Pass", "Chandratal", "Open in Google Maps"):
        assert expected in content
    assert "None" not in content and "null" not in content and "undefined" not in content


@pytest.mark.asyncio
async def test_empty_draft_trip_still_exports_without_blanks(client):
    h = await _auth(client, "pdfdraft@example.com")
    _, tid = await _himachal(client, h)
    resp = await client.get(f"{BASE}/trips/{tid}/export", headers=h)
    assert resp.status_code == 200
    content = _pdf_text(resp.content)
    assert "Dates not decided yet" in content and "has not been written yet" in content
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
