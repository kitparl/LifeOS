"""Travel OS U3 — adventures, drawn routes, GPX import/export and elevation."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from app.modules.files.models import FileRecord
from app.modules.travel import gpx as gpx_module
from app.modules.travel.gpx import GpxError, GpxWaypoint, build_gpx, parse_gpx
from app.modules.travel.models import MapsUsageEvent, TravelRoute
from app.tests.travel_support import auth as _auth
from app.tests.travel_support import connect_google as _connect_google
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import select

BASE = "/api/v1/travel"
pytestmark = pytest.mark.usefixtures("isolated_uploads")

track_points = st.lists(
    st.tuples(
        st.floats(min_value=-89, max_value=89, allow_nan=False),
        st.floats(min_value=-179.9, max_value=179.9, allow_nan=False),
    ),
    min_size=2,
    max_size=60,
)
names = st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc")), min_size=1, max_size=40).filter(
    lambda s: s.strip() == s and s.strip()
)


@given(points=track_points, name=names, wp_names=st.lists(names, max_size=5))
@settings(deadline=None)
def test_gpx_build_parse_round_trip(points, name, wp_names):
    waypoints = [GpxWaypoint(name=n, lat=points[0][0], lng=points[0][1], elevation=100.5) for n in wp_names]
    track = parse_gpx(build_gpx(name, points, waypoints))
    assert track.name == name
    assert len(track.points) == len(points)
    for (lat, lng), (plat, plng) in zip(points, track.points, strict=True):
        assert plat == pytest.approx(lat, abs=1e-7) and plng == pytest.approx(lng, abs=1e-7)
    assert [w.name for w in track.waypoints] == wp_names


@given(points=track_points, elevations=st.lists(st.floats(min_value=-400, max_value=8800), min_size=60, max_size=60))
@settings(deadline=None)
def test_gpx_elevation_round_trip(points, elevations):
    elev = elevations[: len(points)]
    track = parse_gpx(build_gpx("t", points, elevations=elev))
    assert track.has_elevation
    assert track.elevations == pytest.approx([round(e, 1) for e in elev], abs=0.051)


XXE = b"""<?xml version="1.0"?>
<!DOCTYPE gpx [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<gpx version="1.1"><trk><name>&xxe;</name><trkseg>
<trkpt lat="1" lon="1"/><trkpt lat="2" lon="2"/></trkseg></trk></gpx>"""
LAUGHS = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">]>
<gpx><trk><name>&lol2;</name></trk></gpx>"""


@pytest.mark.parametrize(
    "data",
    [
        XXE,
        LAUGHS,
        b"not xml at all",
        b"<kml><Placemark/></kml>",
        b'<gpx><trk><trkseg><trkpt lat="1" lon="1"/></trkseg></trk></gpx>',
        b'<gpx><trk><trkseg><trkpt lat="91" lon="1"/><trkpt lat="1" lon="1"/></trkseg></trk></gpx>',
    ],
)
def test_gpx_rejects_unsafe_or_invalid_files(data):
    with pytest.raises(GpxError):
        parse_gpx(data)


def test_gpx_point_cap():
    with patch.object(gpx_module, "MAX_GPX_POINTS", 3), pytest.raises(GpxError):
        parse_gpx(build_gpx("t", [(1, 1), (1.1, 1.1), (1.2, 1.2), (1.3, 1.3)]))


def test_gpx_prefers_track_and_reads_gpx_1_0_names():
    data = b"""<gpx version="1.0" xmlns="http://www.topografix.com/GPX/1/0"><name>Old style</name>
    <rte><rtept lat="5" lon="5"/><rtept lat="6" lon="6"/></rte>
    <trk><trkseg><trkpt lat="1" lon="1"><ele>10</ele><time>2027-06-17T06:20:00Z</time></trkpt>
    <trkpt lat="1.01" lon="1.01"><ele>25</ele></trkpt></trkseg></trk></gpx>"""
    track = parse_gpx(data)
    assert track.name == "Old style"
    assert track.points == [(1.0, 1.0), (1.01, 1.01)]
    assert track.has_elevation and track.has_time


# ---- API -----------------------------------------------------------------------------------------


def _hampta_gpx() -> bytes:
    points = [(32.2667 + i * 0.001, 77.3667 + i * 0.001) for i in range(50)]
    elevations = [3000 + (i % 10) * 5 for i in range(50)]
    return build_gpx(
        "Hampta Pass trek",
        points,
        [GpxWaypoint("Balu Ka Ghera", 32.28, 77.38, 3600), GpxWaypoint("Summit", 32.3, 77.4, 4270)],
        elevations,
    )


async def _rows(client, model):
    async with client.session_factory() as session:
        return list((await session.execute(select(model))).scalars().all())


async def _adventure(client, h, **extra) -> str:
    resp = await client.post(f"{BASE}/adventures", json={"name": "Hampta Pass", "kind": "trek", **extra}, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()["adventure"]["id"]


@pytest.mark.asyncio
async def test_gpx_preview_then_save_to_adventure_and_export(client):
    h = await _auth(client, "gpx@example.com")
    aid = await _adventure(client, h, difficulty="moderate")
    files = {"file": ("hampta.gpx", _hampta_gpx(), "application/gpx+xml")}

    preview = (await client.post(f"{BASE}/gpx/preview", files=files, headers=h)).json()
    assert preview["name"] == "Hampta Pass trek" and preview["point_count"] == 50
    assert len(preview["points"]) <= 50 and preview["has_elevation"] is True
    assert preview["elevation_gain_m"] > 0 and [w["name"] for w in preview["waypoints"]] == ["Balu Ka Ghera", "Summit"]
    assert await _rows(client, TravelRoute) == []  # preview stores nothing

    saved = await client.post(
        f"{BASE}/gpx", files=files, data={"name": "Hampta (recorded)", "adventure_id": aid}, headers=h
    )
    assert saved.status_code == 201, saved.text
    route = saved.json()
    assert route["source"] == "gpx" and route["distance_m"] == preview["distance_m"]
    records = await _rows(client, FileRecord)
    assert [(r.module, r.entity_id, r.filename) for r in records] == [
        ("travel", route["id"], "Hampta recorded.gpx.xml")
    ]

    detail = (await client.get(f"{BASE}/adventures/{aid}", headers=h)).json()
    assert detail["adventure"]["route_id"] == route["id"]
    assert [w["name"] for w in detail["waypoints"]] == ["Balu Ka Ghera", "Summit"]
    assert detail["elevation_profile"] and len(detail["route_points"]) == len(preview["points"])

    # Elevation came with the GPX, so no Google request is needed.
    again = (await client.post(f"{BASE}/routes/{route['id']}/elevation", headers=h)).json()
    assert again["elevation_gain_m"] == route["elevation_gain_m"]
    assert await _rows(client, MapsUsageEvent) == []

    exported = await client.get(f"{BASE}/routes/{route['id']}/gpx", headers=h)
    assert exported.headers["content-type"].startswith("application/gpx+xml")
    assert 'filename="Hampta recorded.gpx"' in exported.headers["content-disposition"]
    round_trip = parse_gpx(exported.content)
    assert round_trip.name == "Hampta (recorded)" and len(round_trip.points) == len(preview["points"])


@pytest.mark.asyncio
async def test_gpx_upload_is_validated(client):
    h = await _auth(client, "badgpx@example.com")
    bad = await client.post(f"{BASE}/gpx/preview", files={"file": ("x.gpx", XXE, "application/gpx+xml")}, headers=h)
    assert bad.status_code == 400 and "valid GPX" in bad.text
    with patch.object(gpx_module, "MAX_GPX_BYTES", 100):
        from app.modules.travel.api import adventures as adventures_api

        with patch.object(adventures_api, "MAX_GPX_BYTES", 100):
            big = await client.post(
                f"{BASE}/gpx/preview", files={"file": ("x.gpx", _hampta_gpx(), "application/gpx+xml")}, headers=h
            )
    assert big.status_code == 413
    other = await _auth(client, "badgpx2@example.com")
    foreign = await client.post(
        f"{BASE}/gpx",
        files={"file": ("x.gpx", _hampta_gpx(), "application/gpx+xml")},
        data={"name": "x", "adventure_id": await _adventure(client, other)},
        headers=h,
    )
    assert foreign.status_code == 404


@pytest.mark.asyncio
async def test_drawn_route_elevation_needs_a_key_then_is_tracked(client, google):
    h = await _auth(client, "elev@example.com")
    aid = await _adventure(client, h)
    body = {"name": "Ridge", "points": [[32.1, 77.1], [32.15, 77.15], [32.2, 77.2]], "adventure_id": aid}
    route = (await client.post(f"{BASE}/routes", json=body, headers=h)).json()
    assert (await client.get(f"{BASE}/adventures/{aid}", headers=h)).json()["adventure"]["route_id"] == route["id"]

    no_key = await client.post(f"{BASE}/routes/{route['id']}/elevation", headers=h)
    assert no_key.status_code == 400 and "Google Maps key" in no_key.text

    await _connect_google(client, h)
    filled = (await client.post(f"{BASE}/routes/{route['id']}/elevation", headers=h)).json()
    assert filled["elevation_gain_m"] == 20.0 and filled["elevation_loss_m"] == 0.0  # fake: 2000, 2010, 2020
    assert [(e.sku, e.feature) for e in await _rows(client, MapsUsageEvent)] == [("elevation", "adventure_elevation")]

    exported = await client.get(f"{BASE}/routes/{route['id']}/gpx", headers=h)
    assert exported.status_code == 200  # user-drawn routes are exportable


@pytest.mark.asyncio
async def test_google_routes_are_not_exported(client, google):
    h = await _auth(client, "noexport@example.com")
    await _connect_google(client, h)
    pids = []
    for name, lat in (("A", 10.0), ("B", 10.5)):
        pids.append(
            (await client.post(f"{BASE}/places", json={"name": name, "lat": lat, "lng": 76}, headers=h)).json()["id"]
        )
    tid = (
        await client.post(
            f"{BASE}/trips", json={"name": "T", "start_date": "2027-01-01", "end_date": "2027-01-01"}, headers=h
        )
    ).json()["trip"]["id"]
    day = (await client.post(f"{BASE}/trips/{tid}/days/fill", headers=h)).json()["days"][0]["id"]
    for pid in pids:
        await client.post(f"{BASE}/trips/{tid}/places/{pid}", json={"day_id": day}, headers=h)
    route = (await client.post(f"{BASE}/trips/{tid}/route", json={"mode": "driving"}, headers=h)).json()
    assert route["source"] == "google"
    assert (await client.get(f"{BASE}/routes/{route['id']}/gpx", headers=h)).status_code == 400


@pytest.mark.asyncio
async def test_adventure_crud_ownership_and_waypoints(client):
    h = await _auth(client, "adv@example.com")
    other = await _auth(client, "adv2@example.com")
    aid = await _adventure(client, h)
    wps = {
        "waypoints": [
            {"lat": 32.27, "lng": 77.37, "name": "Jobra", "kind": "start"},
            {"lat": 32.3, "lng": 77.4, "name": "Chika", "kind": "camp"},
        ]
    }
    detail = (await client.put(f"{BASE}/adventures/{aid}/waypoints", json=wps, headers=h)).json()
    assert [(w["name"], w["position"]) for w in detail["waypoints"]] == [("Jobra", 0), ("Chika", 1)]
    renamed = {"waypoints": [{**wps["waypoints"][0], "name": "Jobra roadhead"}]}
    detail = (await client.put(f"{BASE}/adventures/{aid}/waypoints", json=renamed, headers=h)).json()
    assert [w["name"] for w in detail["waypoints"]] == ["Jobra roadhead"]

    assert (await client.get(f"{BASE}/adventures/{aid}", headers=other)).status_code == 404
    other_trip = (await client.post(f"{BASE}/trips", json={"name": "Theirs"}, headers=other)).json()["trip"]["id"]
    assert (await client.patch(f"{BASE}/adventures/{aid}", json={"trip_id": other_trip}, headers=h)).status_code == 400
    assert (
        await client.post(f"{BASE}/adventures", json={"name": "x", "kind": "spaceflight"}, headers=h)
    ).status_code == 422

    route = (
        await client.post(
            f"{BASE}/routes", json={"name": "r", "points": [[1, 1], [2, 2]], "adventure_id": aid}, headers=h
        )
    ).json()
    assert (await client.delete(f"{BASE}/adventures/{aid}", headers=h)).status_code == 204
    assert (await client.get(f"{BASE}/routes/{route['id']}", headers=h)).status_code == 404
