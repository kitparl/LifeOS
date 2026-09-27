"""Travel OS U4 — photos (Files module), travel journal, My World and place history."""

from __future__ import annotations

import base64

import pytest
from app.modules.files.models import FileRecord
from app.tests.travel_support import auth as _auth
from sqlalchemy import select

BASE = "/api/v1/travel"
pytestmark = pytest.mark.usefixtures("isolated_uploads")

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


async def _upload(client, h, data=None, **meta):
    form = {k: str(v) for k, v in meta.items()}
    return await client.post(f"{BASE}/photos", files={"file": ("p.png", PNG, "image/png")}, data=form, headers=h)


async def _place(client, h, name="Hampta Pass", lat=32.2667, lng=77.3667) -> str:
    return (await client.post(f"{BASE}/places", json={"name": name, "lat": lat, "lng": lng}, headers=h)).json()["id"]


@pytest.mark.asyncio
async def test_photo_upload_with_confirmed_exif_location_and_links(client):
    h = await _auth(client, "photo@example.com")
    pid = await _place(client, h)
    tid = (await client.post(f"{BASE}/trips", json={"name": "Himachal 2027"}, headers=h)).json()["trip"]["id"]
    resp = await _upload(
        client,
        h,
        lat=32.27,
        lng=77.37,
        location_source="exif",
        taken_at="2027-06-17T06:20:00Z",
        caption="Balu Ka Ghera",
        place_id=pid,
        trip_id=tid,
    )
    assert resp.status_code == 201, resp.text
    photo = resp.json()
    assert photo["location_source"] == "exif" and photo["place_id"] == pid and photo["trip_id"] == tid

    async with client.session_factory() as session:
        (record,) = (await session.execute(select(FileRecord))).scalars().all()
    assert (record.module, record.entity_id, record.visibility) == ("travel", photo["id"], "private")

    # Correcting the location makes it the user's own.
    moved = (await client.patch(f"{BASE}/photos/{photo['id']}", json={"lat": 32.3, "lng": 77.4}, headers=h)).json()
    assert moved["location_source"] == "manual"
    half = await client.patch(f"{BASE}/photos/{photo['id']}", json={"lat": 1}, headers=h)
    assert half.status_code == 400

    by_trip = (await client.get(f"{BASE}/photos", params={"trip_id": tid}, headers=h)).json()
    assert [p["id"] for p in by_trip] == [photo["id"]]
    history = (await client.get(f"{BASE}/places/{pid}/history", headers=h)).json()
    assert history["photo_count"] == 1 and history["recent_photo_ids"] == [photo["id"]]

    assert (await client.delete(f"{BASE}/photos/{photo['id']}", headers=h)).status_code == 204
    async with client.session_factory() as session:
        (record,) = (await session.execute(select(FileRecord))).scalars().all()
    assert record.deleted_at is not None  # soft-deleted through the Files module


@pytest.mark.asyncio
async def test_photo_without_exif_and_bad_inputs(client):
    h = await _auth(client, "nogps@example.com")
    plain = (await _upload(client, h)).json()
    assert plain["lat"] is None and plain["location_source"] is None
    assert (await _upload(client, h, lat=10)).status_code == 422  # lat without lng
    not_image = await client.post(
        f"{BASE}/photos", files={"file": ("notes.txt", b"hello there", "text/plain")}, headers=h
    )
    assert not_image.status_code == 400 and "images" in not_image.text
    other = await _auth(client, "nogps2@example.com")
    foreign_place = await _place(client, other, "Theirs", 1, 1)
    assert (await _upload(client, h, place_id=foreign_place)).status_code == 400


@pytest.mark.asyncio
async def test_travel_journal_allows_many_entries_a_day(client):
    h = await _auth(client, "journal@example.com")
    pid = await _place(client, h)
    tid = (await client.post(f"{BASE}/trips", json={"name": "Himachal 2027"}, headers=h)).json()["trip"]["id"]
    body = {
        "entry_date": "2027-06-17",
        "title": "Trek Day 2",
        "content": "Started at 6:20 AM.",
        "trip_id": tid,
        "place_id": pid,
    }
    first = (await client.post(f"{BASE}/journal", json=body, headers=h)).json()
    second = await client.post(f"{BASE}/journal", json={**body, "title": "Evening"}, headers=h)
    assert second.status_code == 201  # unlike the daily Journal, several entries per day are fine

    photo = (await _upload(client, h, journal_entry_id=first["id"])).json()
    listed = (await client.get(f"{BASE}/journal", params={"trip_id": tid}, headers=h)).json()
    assert {e["title"] for e in listed} == {"Trek Day 2", "Evening"}
    history = (await client.get(f"{BASE}/places/{pid}/history", headers=h)).json()
    assert history["journal_count"] == 2

    updated = (
        await client.patch(f"{BASE}/journal/{first['id']}", json={"content": "Weather was clear."}, headers=h)
    ).json()
    assert updated["content"] == "Weather was clear."
    assert (await client.delete(f"{BASE}/journal/{first['id']}", headers=h)).status_code == 204
    remaining = (await client.get(f"{BASE}/photos", params={"journal_entry_id": first["id"]}, headers=h)).json()
    assert remaining == []  # photo kept, link dropped
    assert (await client.get(f"{BASE}/photos", headers=h)).json()[0]["id"] == photo["id"]

    other = await _auth(client, "journal2@example.com")
    assert (await client.get(f"{BASE}/journal/{second.json()['id']}", headers=other)).status_code == 404
    assert (await client.post(f"{BASE}/journal", json={**body, "trip_id": tid}, headers=other)).status_code == 400


@pytest.mark.asyncio
async def test_my_world_markers_and_counts(client):
    h = await _auth(client, "world@example.com")
    manali = await _place(client, h, "Manali", 32.2432, 77.1892)
    await _place(client, h, "Goa", 15.3, 74.1)
    tid = (
        await client.post(
            f"{BASE}/trips", json={"name": "Himachal", "start_date": "2027-06-12", "end_date": "2027-06-13"}, headers=h
        )
    ).json()["trip"]["id"]
    await client.post(f"{BASE}/trips/{tid}/places/{manali}", headers=h)
    await client.post(f"{BASE}/trips/{tid}/confirm", headers=h)
    await client.post(f"{BASE}/trips/{tid}/complete", headers=h)
    aid = (await client.post(f"{BASE}/adventures", json={"name": "Hampta", "trip_id": tid}, headers=h)).json()[
        "adventure"
    ]["id"]
    await client.post(
        f"{BASE}/routes", json={"name": "r", "points": [[32.27, 77.37], [32.3, 77.4]], "adventure_id": aid}, headers=h
    )
    await _upload(client, h, lat=32.28, lng=77.38, caption="Camp")
    await _upload(client, h)  # no location: counted nowhere on the map

    world = (await client.get(f"{BASE}/world", headers=h)).json()
    assert world["counts"] == {
        "wishlist": 1,
        "planned": 0,
        "visited": 1,
        "favourite": 0,
        "trips": 1,
        "completed_trips": 1,
        "adventures": 1,
        "photos": 1,
    }
    kinds = sorted((m["kind"], m["label"]) for m in world["markers"])
    assert kinds == [
        ("adventure", "Hampta"),
        ("photo", "Camp"),
        ("place", "Goa"),
        ("place", "Manali"),
        ("trip", "Himachal"),
    ]
    adventure = next(m for m in world["markers"] if m["kind"] == "adventure")
    assert (adventure["lat"], adventure["lng"], adventure["trip_id"]) == (32.27, 77.37, tid)
    assert (await client.get(f"{BASE}/markers", headers=h)).json() == world["markers"]
