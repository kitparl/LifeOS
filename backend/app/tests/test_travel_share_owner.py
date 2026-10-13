"""Shared trip plans: the owner's side (link, settings, versions, lock, apply). Example-based tests."""

from __future__ import annotations

import pytest
from app.core.short_codes import SHORT_CODE_ALPHABET
from app.modules.travel.models import (
    TravelItineraryDay,
    TravelPlace,
    TravelShareEvent,
    TravelShareVersion,
    TravelTripShare,
)
from app.modules.travel.schemas.plan_document import PlanDay, PlanDocument, PlanPlace, PlanStop
from app.tests.share_support import BASE, add_friend_plan, rows, shared_trip
from app.tests.test_travel_export import _pdf_text
from app.tests.travel_support import auth as _auth

pytestmark = pytest.mark.usefixtures("isolated_uploads")


@pytest.fixture(autouse=True)
def _no_network_tiles(monkeypatch):
    from app.modules.travel.services import export_service

    monkeypatch.setattr(export_service.TileBasemap, "from_settings", classmethod(lambda cls: None))


def _share_url(tid: str, suffix: str = "") -> str:
    return f"{BASE}/trips/{tid}/share{suffix}"


async def _versions(client, h, tid) -> list[dict]:
    resp = await client.get(_share_url(tid, "/versions"), headers=h)
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_create_link_snapshots_the_itinerary_as_the_original(client):
    h = await _auth(client, "owner1@example.com")
    tid, _, share = await shared_trip(client, h)
    await client.patch(f"{BASE}/trips/{tid}", json={"notes": "door code 4512", "description": "Mountains"}, headers=h)

    assert len(share["code"]) == 8 and set(share["code"]) <= set(SHORT_CODE_ALPHABET)
    assert share["url_path"] == f"/t/{share['code']}" and share["state"] == "open"
    versions = await _versions(client, h, tid)
    assert [v["kind"] for v in versions] == ["original"]
    original = versions[0]
    assert original["label"] == "Original" and original["summary"]["stops"] == 3
    assert original["summary"] | {"km": 0} == {"days": 10, "stops": 3, "added": 0, "removed": 0, "changed": 0, "km": 0}
    detail = (await client.get(_share_url(tid, f"/versions/{original['id']}"), headers=h)).json()
    day1 = detail["document"]["days"][0]["stops"]
    assert [s["title"] for s in day1] == ["Manali", "Hampta Pass"]
    assert day1[0]["place"]["lat"] == pytest.approx(32.2432)
    assert "door code" not in str(detail["document"])  # trip notes never enter a plan

    assert (await client.post(_share_url(tid), headers=h)).status_code == 409


@pytest.mark.asyncio
async def test_original_does_not_follow_later_trip_edits(client):
    h = await _auth(client, "owner2@example.com")
    tid, _, _ = await shared_trip(client, h)
    detail = (await client.get(f"{BASE}/trips/{tid}", headers=h)).json()
    await client.patch(
        f"{BASE}/trips/{tid}/items/{detail['days'][0]['items'][0]['id']}", json={"title": "Renamed"}, headers=h
    )
    original = (await _versions(client, h, tid))[0]
    doc = (await client.get(_share_url(tid, f"/versions/{original['id']}"), headers=h)).json()["document"]
    assert doc["days"][0]["stops"][0]["title"] == "Manali"


@pytest.mark.asyncio
async def test_another_user_gets_404_on_every_owner_endpoint(client):
    owner = await _auth(client, "owner3@example.com")
    other = await _auth(client, "intruder3@example.com")
    tid, _, _ = await shared_trip(client, owner)
    vid = (await _versions(client, owner, tid))[0]["id"]
    calls = [
        ("post", "", None),
        ("get", "", None),
        ("patch", "/settings", {"require_google": True}),
        ("post", "/revoke", None),
        ("post", "/new-link", None),
        ("post", "/lock", {"version_id": vid}),
        ("post", "/unlock", None),
        ("get", "/versions", None),
        ("post", "/versions", None),
        ("get", f"/versions/{vid}", None),
        ("patch", f"/versions/{vid}", {"label": "Mine now"}),
        ("delete", f"/versions/{vid}", None),
        ("post", f"/versions/{vid}/apply", None),
        ("get", f"/versions/{vid}/export", None),
        ("delete", "/contributors/someone", None),
        ("get", "/events", None),
    ]
    for method, suffix, body in calls:
        kwargs = {"headers": other} | ({"json": body} if body is not None else {})
        resp = await getattr(client, method)(_share_url(tid, suffix), **kwargs)
        assert resp.status_code == 404, (method, suffix, resp.status_code)
    assert (await client.get(_share_url(tid), headers=owner)).json()["state"] == "open"


@pytest.mark.asyncio
async def test_settings_revoke_and_new_link(client):
    h = await _auth(client, "owner4@example.com")
    tid, _, share = await shared_trip(client, h)
    body = {"require_google": True, "allowed_emails": [" Asha@Gmail.com", "asha@gmail.com", "ravi@gmail.com"]}
    updated = (await client.patch(_share_url(tid, "/settings"), json=body, headers=h)).json()
    assert updated["require_google"] is True and updated["allowed_emails"] == ["asha@gmail.com", "ravi@gmail.com"]
    bad = await client.patch(_share_url(tid, "/settings"), json={"allowed_emails": ["not-an-email"]}, headers=h)
    assert bad.status_code == 422

    revoked = (await client.post(_share_url(tid, "/revoke"), headers=h)).json()
    assert revoked["state"] == "revoked" and revoked["revoked_at"]
    vid = (await _versions(client, h, tid))[0]["id"]
    assert (await client.post(_share_url(tid, "/lock"), json={"version_id": vid}, headers=h)).status_code == 409

    fresh = (await client.post(_share_url(tid, "/new-link"), headers=h)).json()
    assert fresh["state"] == "open" and fresh["code"] != share["code"] and fresh["revoked_at"] is None
    assert len(await _versions(client, h, tid)) == 1  # plans survive a new link


@pytest.mark.asyncio
async def test_owner_snapshots_are_capped_and_listed_latest_first(client):
    h = await _auth(client, "owner5@example.com")
    tid, _, _ = await shared_trip(client, h)
    labels = []
    for _ in range(5):
        resp = await client.post(_share_url(tid, "/versions"), headers=h)
        assert resp.status_code == 201
        labels.append(resp.json()["label"])
    assert labels[0] == "Traveller's plan" and labels[1] == "Traveller's plan 2"
    assert (await client.post(_share_url(tid, "/versions"), headers=h)).status_code == 409

    listed = await _versions(client, h, tid)
    stamps = [v["updated_at"] for v in listed]
    assert stamps == sorted(stamps, reverse=True)
    oldest = listed[-1]
    renamed = await client.patch(_share_url(tid, f"/versions/{oldest['id']}"), json={"label": "  First  "}, headers=h)
    assert renamed.json()["label"] == "First"
    assert (await _versions(client, h, tid))[-1]["id"] == oldest["id"]  # a rename does not reorder


@pytest.mark.asyncio
async def test_delete_rules(client):
    h = await _auth(client, "owner6@example.com")
    tid, _, share = await shared_trip(client, h)
    original = (await _versions(client, h, tid))[0]["id"]
    mine = (await client.post(_share_url(tid, "/versions"), headers=h)).json()["id"]
    assert (await client.delete(_share_url(tid, f"/versions/{original}"), headers=h)).status_code == 409
    await client.post(_share_url(tid, "/lock"), json={"version_id": mine, "apply": False}, headers=h)
    assert (await client.delete(_share_url(tid, f"/versions/{mine}"), headers=h)).status_code == 409
    await client.post(_share_url(tid, "/unlock"), headers=h)
    assert (await client.delete(_share_url(tid, f"/versions/{mine}"), headers=h)).status_code == 204
    assert (await client.get(_share_url(tid, f"/versions/{mine}"), headers=h)).status_code == 404


def _friend_doc(places_existing: tuple[float, float]) -> PlanDocument:
    lat, lng = places_existing
    return PlanDocument(
        days=[
            PlanDay(title="Arrive", stops=[PlanStop(id="s1", title="Manali again", place=PlanPlace(name="Manali", lat=lat, lng=lng))]),
            PlanDay(stops=[PlanStop(id="s2", title="Cafe 1947", kind="food", stay="Riverside camp")]),
            PlanDay(
                stops=[
                    PlanStop(
                        id="s3",
                        title="Spiti",
                        place=PlanPlace(name="Kaza", lat=32.2276, lng=78.0710, google_place_id="ChIJkaza123"),
                        links=["https://example.com/kaza"],
                    )
                ]
            ),
        ]
    )


@pytest.mark.asyncio
async def test_lock_with_apply_replaces_the_itinerary_and_keeps_a_backup(client):
    h = await _auth(client, "owner7@example.com")
    tid, _, share = await shared_trip(client, h)
    vid = await add_friend_plan(client, share["id"], _friend_doc((32.2432, 77.1892)))
    places_before = len(await rows(client, TravelPlace))

    resp = await client.post(_share_url(tid, "/lock"), json={"version_id": vid, "apply": True}, headers=h)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["share"]["state"] == "locked" and body["share"]["locked_version_id"] == vid
    applied = body["applied"]
    assert applied | {"backup_version_id": "x"} == {
        "days": 3, "items": 3, "places_created": 1, "places_reused": 1, "backup_version_id": "x",
        "end_date": "2027-06-14", "end_date_changed": True,
    }
    assert len(await rows(client, TravelPlace)) == places_before + 1

    trip = (await client.get(f"{BASE}/trips/{tid}", headers=h)).json()
    assert trip["trip"]["end_date"] == "2027-06-14"
    assert [d["day_date"] for d in trip["days"]] == ["2027-06-12", "2027-06-13", "2027-06-14"]
    assert [[i["title"] for i in d["items"]] for d in trip["days"]] == [["Manali again"], ["Cafe 1947"], ["Spiti"]]
    assert trip["days"][1]["items"][0]["accommodation"] == "Riverside camp"
    assert trip["days"][0]["title"] == "Arrive"

    versions = await _versions(client, h, tid)
    backup = next(v for v in versions if v["kind"] == "backup")
    assert backup["id"] == applied["backup_version_id"] and backup["label"] == "Before applying Asha's plan"
    assert next(v for v in versions if v["id"] == vid)["is_locked"] is True
    actions = sorted(e.action for e in await rows(client, TravelShareEvent))
    assert actions == ["apply", "create", "lock"]

    # Apply is reversible: restoring the backup brings the original 10 days back.
    restored = await client.post(_share_url(tid, f"/versions/{backup['id']}/apply"), headers=h)
    assert restored.status_code == 200
    trip = (await client.get(f"{BASE}/trips/{tid}", headers=h)).json()
    assert len(trip["days"]) == 10 and [i["title"] for i in trip["days"][0]["items"]] == ["Manali", "Hampta Pass"]

    assert (await client.post(_share_url(tid, "/unlock"), headers=h)).json()["state"] == "open"
    assert (await client.post(_share_url(tid, "/unlock"), headers=h)).status_code == 409


@pytest.mark.asyncio
async def test_lock_without_apply_leaves_the_trip_alone_and_backups_cannot_be_final(client):
    h = await _auth(client, "owner8@example.com")
    tid, _, share = await shared_trip(client, h)
    vid = await add_friend_plan(client, share["id"], _friend_doc((1.0, 1.0)))
    body = (await client.post(_share_url(tid, "/lock"), json={"version_id": vid, "apply": False}, headers=h)).json()
    assert body["applied"] is None
    assert len(await rows(client, TravelItineraryDay)) == 10

    await client.post(_share_url(tid, "/unlock"), headers=h)
    backup_id = (await client.post(_share_url(tid, f"/versions/{vid}/apply"), headers=h)).json()["backup_version_id"]
    assert (await client.post(_share_url(tid, "/lock"), json={"version_id": backup_id}, headers=h)).status_code == 409


@pytest.mark.asyncio
async def test_backups_are_pruned_to_the_latest_five(client):
    h = await _auth(client, "owner9@example.com")
    tid, _, share = await shared_trip(client, h)
    vid = await add_friend_plan(client, share["id"], _friend_doc((1.0, 1.0)))
    for _ in range(7):
        assert (await client.post(_share_url(tid, f"/versions/{vid}/apply"), headers=h)).status_code == 200
    backups = [v for v in await rows(client, TravelShareVersion) if v.kind == "backup"]
    assert len(backups) == 5


@pytest.mark.asyncio
async def test_version_pdf_and_trip_pdf_footer_link(client):
    h = await _auth(client, "owner10@example.com")
    tid, _, share = await shared_trip(client, h)
    vid = await add_friend_plan(client, share["id"], _friend_doc((32.2432, 77.1892)))
    pdf = await client.get(_share_url(tid, f"/versions/{vid}/export"), headers=h)
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    text = _pdf_text(pdf.content)
    assert "Cafe 1947" in text and "Kaza" in text

    guide = _pdf_text((await client.get(f"{BASE}/trips/{tid}/export", headers=h)).content)
    assert f"/t/{share['code']}" in guide
    await client.post(_share_url(tid, "/revoke"), headers=h)
    guide = _pdf_text((await client.get(f"{BASE}/trips/{tid}/export", headers=h)).content)
    assert "/t/" not in guide


@pytest.mark.asyncio
async def test_deleting_the_trip_removes_its_share(client):
    h = await _auth(client, "owner11@example.com")
    tid, _, share = await shared_trip(client, h)
    await add_friend_plan(client, share["id"], _friend_doc((1.0, 1.0)))
    assert (await client.delete(f"{BASE}/trips/{tid}", headers=h)).status_code == 204
    assert await rows(client, TravelTripShare) == []
    assert await rows(client, TravelShareVersion) == []
    assert await rows(client, TravelShareEvent) == []


@pytest.mark.asyncio
async def test_events_are_listed_newest_first(client):
    h = await _auth(client, "owner12@example.com")
    tid, _, _ = await shared_trip(client, h)
    await client.post(_share_url(tid, "/revoke"), headers=h)
    events = (await client.get(_share_url(tid, "/events"), headers=h)).json()
    assert [e["action"] for e in events] == ["revoke", "create"]
    assert all(e["actor"] == "owner" for e in events)
