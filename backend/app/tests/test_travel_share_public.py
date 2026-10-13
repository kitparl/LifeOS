"""Shared trip plans: the public friend planner API and the /t/<code> page. Example-based tests."""

from __future__ import annotations

import hashlib
import json

import httpx
import pytest
from app.main import app
from app.modules.auth.models import User
from app.modules.notifications.models import Notification
from app.modules.travel import maps_links, share_page
from app.modules.travel import share_token as share_token_module
from app.modules.travel.api import shared as shared_api
from app.modules.travel.models import MapsUsageEvent, TravelShareContributor, TravelShareVersion
from app.modules.travel.services import shared_plan_service
from app.tests.google_support import google_token
from app.tests.share_support import BASE, rows, shared_trip
from app.tests.travel_support import auth as _auth
from app.tests.travel_support import connect_google as _connect_google
from sqlalchemy import func, select

SHARED = f"{BASE}/shared"
pytestmark = pytest.mark.usefixtures("isolated_uploads", "fake_google_identity")


@pytest.fixture(autouse=True)
def _fresh_limiters():
    shared_api.reset_limiters()
    shared_plan_service.reset_limiters()
    share_page.reset_limiter()
    yield
    shared_api.reset_limiters()
    shared_plan_service.reset_limiters()
    share_page.reset_limiter()


# ---- helpers ------------------------------------------------------------------------------------


async def _setup(client, email: str) -> tuple[dict, str, dict]:
    h = await _auth(client, email)
    tid, _, share = await shared_trip(client, h)
    await client.patch(f"{BASE}/trips/{tid}", json={"notes": "door code 4512"}, headers=h)
    return h, tid, share


async def _join(client, code: str, name: str = "Asha") -> dict:
    resp = await client.post(f"{SHARED}/{code}/join/name", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _tok(joined: dict) -> dict[str, str]:
    return {"X-Share-Token": joined["token"]}


async def _start(client, code: str, joined: dict) -> dict:
    resp = await client.post(f"{SHARED}/{code}/me/plan", headers=_tok(joined))
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


async def _save(client, code: str, joined: dict, doc: dict, revision: int | None) -> httpx.Response:
    headers = _tok(joined) | ({"If-Match": f'"{revision}"'} if revision is not None else {})
    return await client.put(f"{SHARED}/{code}/me/plan", json=doc, headers=headers)


def _with_new_stop(doc: dict, title: str = "Cafe 1947") -> dict:
    doc = json.loads(json.dumps(doc))
    doc["days"][0]["stops"].append({"id": f"new-{title.replace(' ', '-')}", "title": title, "kind": "food"})
    return doc


def _all_keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _all_keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _all_keys(v)}
    return set()


# ---- viewing ------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_anyone_with_the_link_sees_the_original_and_nothing_is_created(client):
    h, tid, share = await _setup(client, "pub1@example.com")
    resp = await client.get(f"{SHARED}/{share['code']}")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store" and resp.headers["referrer-policy"] == "no-referrer"
    view = resp.json()
    assert view["trip"]["name"] == "Himachal 2027" and view["owner_name"] == "Traveller"
    assert view["state"] == "open" and view["is_final"] is False and view["viewer_is_owner"] is False
    assert view["names_allowed"] is True and view["google_enabled"] is True
    assert [s["title"] for s in view["plan"]["days"][0]["stops"]] == ["Manali", "Hampta Pass"]
    assert await rows(client, TravelShareContributor) == []

    assert view["manage_path"] is None
    owner_view = (await client.get(f"{SHARED}/{share['code']}", headers=h)).json()
    assert owner_view["viewer_is_owner"] is True and owner_view["manage_path"] == f"/travel/trips/{tid}?panel=share"


@pytest.mark.asyncio
async def test_unknown_code_is_404_and_malformed_code_is_rejected(client):
    assert (await client.get(f"{SHARED}/abcdefgh")).status_code == 404
    assert (await client.get(f"{SHARED}/ABC")).status_code == 422


# ---- identity -----------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_join_with_name_stores_only_the_secret_hash(client):
    _, _, share = await _setup(client, "pub2@example.com")
    joined = await _join(client, share["code"])
    assert joined["contributor"]["kind"] == "name" and joined["plan"] is None
    [contributor] = await rows(client, TravelShareContributor)
    assert contributor.secret_hash == hashlib.sha256(joined["device_secret"].encode()).hexdigest()
    assert joined["device_secret"] not in json.dumps({c.name: str(getattr(contributor, c.name)) for c in contributor.__table__.columns})

    renewed = await client.post(f"{SHARED}/{share['code']}/session", json={"device_secret": joined["device_secret"]})
    assert renewed.status_code == 200 and renewed.json()["contributor"]["id"] == joined["contributor"]["id"]
    assert "device_secret" not in renewed.json()
    wrong = await client.post(f"{SHARED}/{share['code']}/session", json={"device_secret": "x" * 32})
    assert wrong.status_code == 401


@pytest.mark.asyncio
async def test_same_google_account_is_the_same_friend_on_every_device(client):
    _, _, share = await _setup(client, "pub3@example.com")
    code = share["code"]
    phone = (await client.post(f"{SHARED}/{code}/join/google", json={"credential": google_token("asha@gmail.com", sub="g-1", name="Asha Rao")})).json()
    await _start(client, code, phone)
    tablet = (await client.post(f"{SHARED}/{code}/join/google", json={"credential": google_token("asha@gmail.com", sub="g-1")})).json()
    assert tablet["contributor"]["id"] == phone["contributor"]["id"]
    assert tablet["contributor"]["display_name"] == "Asha Rao" and tablet["plan"] is not None
    assert len(await rows(client, TravelShareContributor)) == 1
    # One active device secret: signing in on the tablet retires the phone's silent renewal.
    old = await client.post(f"{SHARED}/{code}/session", json={"device_secret": phone["device_secret"]})
    assert old.status_code == 401


@pytest.mark.asyncio
async def test_owner_signing_in_with_google_creates_nothing(client):
    _, _, share = await _setup(client, "pub4@example.com")
    resp = await client.post(f"{SHARED}/{share['code']}/join/google", json={"credential": google_token("PUB4@example.com")})
    assert resp.status_code == 201 and resp.json() == {"owner": True}
    assert await rows(client, TravelShareContributor) == []


@pytest.mark.asyncio
async def test_require_google_and_allow_list_are_enforced(client):
    h, tid, share = await _setup(client, "pub5@example.com")
    code = share["code"]
    await client.patch(f"{BASE}/trips/{tid}/share/settings", json={"require_google": True}, headers=h)
    assert (await client.get(f"{SHARED}/{code}")).json()["names_allowed"] is False
    assert (await client.post(f"{SHARED}/{code}/join/name", json={"name": "Asha"})).status_code == 403

    await client.patch(
        f"{BASE}/trips/{tid}/share/settings",
        json={"require_google": False, "allowed_emails": ["ravi@gmail.com"]},
        headers=h,
    )
    assert (await client.post(f"{SHARED}/{code}/join/name", json={"name": "Asha"})).status_code == 403
    stranger = await client.post(f"{SHARED}/{code}/join/google", json={"credential": google_token("asha@gmail.com", sub="g-a")})
    assert stranger.status_code == 403
    invited = await client.post(f"{SHARED}/{code}/join/google", json={"credential": google_token("Ravi@Gmail.com", sub="g-r")})
    assert invited.status_code == 201
    bad = await client.post(f"{SHARED}/{code}/join/google", json={"credential": google_token("ravi@gmail.com", aud="someone-else")})
    assert bad.status_code == 401


@pytest.mark.asyncio
async def test_a_link_takes_at_most_twenty_friends(client, monkeypatch):
    _, _, share = await _setup(client, "pub6@example.com")
    monkeypatch.setattr(shared_api, "_join_ip", shared_api.SlidingWindowLimiter(limit=100, window_seconds=600))
    for i in range(20):
        await _join(client, share["code"], f"Friend {i}")
    assert (await client.post(f"{SHARED}/{share['code']}/join/name", json={"name": "One more"})).status_code == 409


@pytest.mark.asyncio
async def test_name_friend_can_switch_to_google_and_keep_their_plan(client):
    _, _, share = await _setup(client, "pub7@example.com")
    code = share["code"]
    joined = await _join(client, code)
    plan = await _start(client, code, joined)
    up = await client.post(f"{SHARED}/{code}/me/upgrade-google", json={"credential": google_token("asha@gmail.com", sub="g-up")}, headers=_tok(joined))
    assert up.status_code == 200 and up.json()["contributor"]["kind"] == "google"
    again = (await client.post(f"{SHARED}/{code}/join/google", json={"credential": google_token("asha@gmail.com", sub="g-up")})).json()
    assert again["plan"]["id"] == plan["id"]


# ---- the share token is never a LifeOS login ---------------------------------------------------


def _bearer_operations() -> list[tuple[str, str]]:
    """Every operation that reads the `Authorization: Bearer` header (the LifeOS session)."""
    ops = []
    for path, item in app.openapi()["paths"].items():
        for method, op in item.items():
            if any("HTTPBearer" in req for req in op.get("security", [])):
                ops.append((method, path))
    return ops


@pytest.mark.asyncio
async def test_share_token_is_rejected_by_every_lifeos_endpoint_and_never_creates_a_user(client):
    _, _, share = await _setup(client, "pub8@example.com")
    joined = await _join(client, share["code"])
    async with client.session_factory() as session:
        users_before = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    ops = _bearer_operations()
    assert len(ops) > 100  # the whole authenticated API, not a handful
    for method, path in ops:
        url = path.replace("{", "").replace("}", "")  # any placeholder value: auth runs first
        resp = await client.request(method.upper(), url, headers={"Authorization": f"Bearer {joined['token']}"})
        assert resp.status_code == 401, (method, path, resp.status_code)
        assert "refresh_token" not in resp.cookies
    async with client.session_factory() as session:
        assert (await session.execute(select(func.count()).select_from(User))).scalar_one() == users_before


@pytest.mark.asyncio
async def test_lifeos_tokens_and_tokens_for_other_links_are_not_share_tokens(client):
    h, _, share = await _setup(client, "pub9@example.com")
    _, _, other = await shared_trip(client, await _auth(client, "pub9b@example.com"))
    stranger = await _join(client, other["code"])
    me = f"{SHARED}/{share['code']}/me"
    assert (await client.get(me)).status_code == 401
    assert (await client.get(me, headers={"X-Share-Token": h["Authorization"].split()[1]})).status_code == 401
    assert (await client.get(me, headers=_tok(stranger))).status_code == 401
    assert (await client.get(me, headers={"X-Share-Token": "garbage"})).status_code == 401
    token, _ = share_token_module.issue(share["id"], "not-a-friend")
    assert (await client.get(me, headers={"X-Share-Token": token})).status_code == 401


# ---- plans: isolation, revisions, limits --------------------------------------------------------


@pytest.mark.asyncio
async def test_friends_only_ever_touch_their_own_plan(client):
    _, _, share = await _setup(client, "pub10@example.com")
    code = share["code"]
    asha, ravi = await _join(client, code, "Asha"), await _join(client, code, "Ravi")
    a_plan, r_plan = await _start(client, code, asha), await _start(client, code, ravi)
    assert a_plan["id"] != r_plan["id"]
    saved = await _save(client, code, asha, _with_new_stop(a_plan["document"]), a_plan["revision"])
    assert saved.status_code == 200
    ravi_now = (await client.get(f"{SHARED}/{code}/me", headers=_tok(ravi))).json()["plan"]
    assert ravi_now["revision"] == 1 and "Cafe 1947" not in json.dumps(ravi_now)
    # Starting again is idempotent.
    assert (await client.post(f"{SHARED}/{code}/me/plan", headers=_tok(asha))).status_code == 200


@pytest.mark.asyncio
async def test_revision_checks_stop_silent_overwrites(client):
    _, _, share = await _setup(client, "pub11@example.com")
    code = share["code"]
    joined = await _join(client, code)
    plan = await _start(client, code, joined)
    doc = _with_new_stop(plan["document"])
    assert (await _save(client, code, joined, doc, None)).status_code == 428
    first = await _save(client, code, joined, doc, plan["revision"])
    assert first.status_code == 200 and first.json()["revision"] == 2 and first.headers["etag"] == '"2"'
    stale = await _save(client, code, joined, doc, plan["revision"])
    assert stale.status_code == 412 and stale.json()["detail"]["revision"] == 2

    reset = await client.post(f"{SHARED}/{code}/me/plan/reset", headers=_tok(joined) | {"If-Match": '"2"'})
    assert reset.status_code == 200 and reset.json()["revision"] == 3
    assert "Cafe 1947" not in json.dumps(reset.json()["document"])


@pytest.mark.asyncio
async def test_size_limits(client):
    _, _, share = await _setup(client, "pub12@example.com")
    code = share["code"]
    joined = await _join(client, code)
    plan = await _start(client, code, joined)
    too_many_days = {"days": [{"stops": []} for _ in range(121)]}
    assert (await _save(client, code, joined, too_many_days, plan["revision"])).status_code == 422
    long_title = {"days": [{"stops": [{"id": "s", "title": "x" * 201}]}]}
    assert (await _save(client, code, joined, long_title, plan["revision"])).status_code == 422
    duplicate_ids = {"days": [{"stops": [{"id": "s", "title": "a"}, {"id": "s", "title": "b"}]}]}
    assert (await _save(client, code, joined, duplicate_ids, plan["revision"])).status_code == 422
    bad_link = {"days": [{"stops": [{"id": "s", "title": "a", "links": ["javascript:alert(1)"]}]}]}
    assert (await _save(client, code, joined, bad_link, plan["revision"])).status_code == 422
    huge = {"days": [{"notes": "x" * 9_000, "stops": []} for _ in range(70)]}
    resp = await client.put(
        f"{SHARED}/{code}/me/plan", content=json.dumps(huge), headers=_tok(joined) | {"If-Match": '"1"', "Content-Type": "application/json"}
    )
    assert resp.status_code == 413


@pytest.mark.asyncio
async def test_sending_notifies_the_owner_and_shows_latest_first(client):
    h, tid, share = await _setup(client, "pub13@example.com")
    code = share["code"]
    asha, ravi = await _join(client, code, "Asha"), await _join(client, code, "Ravi")
    a_plan = await _start(client, code, asha)
    await _start(client, code, ravi)
    sent = await client.post(f"{SHARED}/{code}/me/plan/submit", json={"message": "  Added a cafe!  "}, headers=_tok(asha))
    assert sent.status_code == 200 and sent.json()["status"] == "submitted"
    [note] = await rows(client, Notification)
    assert note.message == "Asha sent you a plan for Himachal 2027" and note.route == f"/travel/trips/{tid}?panel=share"

    await _save(client, code, asha, _with_new_stop(a_plan["document"]), a_plan["revision"])
    versions = (await client.get(f"{BASE}/trips/{tid}/share/versions", headers=h)).json()
    assert [v["label"] for v in versions][0] == "Asha's plan"
    top = versions[0]
    assert top["status"] == "submitted" and top["edited_since_sent"] is True and top["message"] == "Added a cafe!"
    assert top["author_kind"] == "contributor" and top["summary"]["added"] == 1
    stamps = [v["updated_at"] for v in versions]
    assert stamps == sorted(stamps, reverse=True)


# ---- locked, revoked, removed: every write is rejected -------------------------------------------


def _writes(code: str, revision: int) -> list[tuple[str, str, dict]]:
    base = f"{SHARED}/{code}"
    doc = {"days": []}
    return [
        ("post", f"{base}/join/name", {"json": {"name": "Late"}}),
        ("post", f"{base}/join/google", {"json": {"credential": google_token("late@gmail.com", sub="g-late")}}),
        ("post", f"{base}/me/upgrade-google", {"json": {"credential": google_token("x@gmail.com", sub="g-x")}}),
        ("post", f"{base}/me/plan", {}),
        ("put", f"{base}/me/plan", {"json": doc, "if_match": revision}),
        ("post", f"{base}/me/plan/reset", {"if_match": revision}),
        ("post", f"{base}/me/plan/submit", {"json": {}}),
        ("get", f"{base}/maps/autocomplete?q=manali&session=abcdefgh1", {}),
        ("get", f"{base}/maps/place/ChIJmanali", {}),
        ("get", f"{base}/resolve-link?url=https://www.google.com/maps/@1,2,3z", {}),
    ]


async def _call(client, joined: dict, method: str, url: str, opts: dict) -> httpx.Response:
    headers = _tok(joined) | ({"If-Match": f'"{opts["if_match"]}"'} if "if_match" in opts else {})
    return await client.request(method.upper(), url, json=opts.get("json"), headers=headers)


@pytest.mark.asyncio
async def test_locked_means_409_on_every_write_and_the_final_plan_is_shown(client):
    h, tid, share = await _setup(client, "pub14@example.com")
    code = share["code"]
    joined = await _join(client, code)
    plan = await _start(client, code, joined)
    await _save(client, code, joined, _with_new_stop(plan["document"]), plan["revision"])
    await client.post(f"{BASE}/trips/{tid}/share/lock", json={"version_id": plan["id"], "apply": False}, headers=h)

    for method, url, opts in _writes(code, 2):
        resp = await _call(client, joined, method, url, opts)
        assert resp.status_code == 409, (method, url, resp.status_code)
    view = (await client.get(f"{SHARED}/{code}")).json()
    assert view["is_final"] is True and view["state"] == "locked"
    assert "Cafe 1947" in json.dumps(view["plan"])
    mine = (await client.get(f"{SHARED}/{code}/me", headers=_tok(joined))).json()
    assert mine["plan"]["revision"] == 2  # the friend's own plan is kept, frozen


@pytest.mark.asyncio
async def test_revoked_link_is_410_everywhere_and_a_new_link_kills_the_old_code(client):
    h, tid, share = await _setup(client, "pub15@example.com")
    code = share["code"]
    joined = await _join(client, code)
    await client.post(f"{BASE}/trips/{tid}/share/revoke", headers=h)
    assert (await client.get(f"{SHARED}/{code}")).status_code == 410
    assert (await client.get(f"{SHARED}/{code}/me", headers=_tok(joined))).status_code == 410
    assert (await client.post(f"{SHARED}/{code}/session", json={"device_secret": joined["device_secret"]})).status_code == 410
    for method, url, opts in _writes(code, 1):
        assert (await _call(client, joined, method, url, opts)).status_code == 410, (method, url)

    fresh = (await client.post(f"{BASE}/trips/{tid}/share/new-link", headers=h)).json()
    assert (await client.get(f"{SHARED}/{code}")).status_code == 404
    assert (await client.get(f"{SHARED}/{fresh['code']}")).status_code == 200


@pytest.mark.asyncio
async def test_removed_friend_cannot_write_or_sign_back_in(client):
    h, tid, share = await _setup(client, "pub16@example.com")
    code = share["code"]
    joined = (await client.post(f"{SHARED}/{code}/join/google", json={"credential": google_token("asha@gmail.com", sub="g-rm")})).json()
    await _start(client, code, joined)
    await client.delete(f"{BASE}/trips/{tid}/share/contributors/{joined['contributor']['id']}", headers=h)
    for method, url, opts in _writes(code, 1)[2:]:
        assert (await _call(client, joined, method, url, opts)).status_code == 403, (method, url)
    assert (await client.post(f"{SHARED}/{code}/session", json={"device_secret": joined["device_secret"]})).status_code == 401
    back = await client.post(f"{SHARED}/{code}/join/google", json={"credential": google_token("asha@gmail.com", sub="g-rm")})
    assert back.status_code == 403
    versions = (await client.get(f"{BASE}/trips/{tid}/share/versions", headers=h)).json()
    assert any(v["contributor_removed"] for v in versions)  # their plan is kept


# ---- nothing private leaks ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_responses_never_contain_private_fields(client):
    h, tid, share = await _setup(client, "pub17@example.com")
    code = share["code"]
    ravi = (await client.post(f"{SHARED}/{code}/join/google", json={"credential": google_token("ravi@gmail.com", sub="g-ravi")})).json()
    asha = await _join(client, code, "Asha")
    bodies = [
        (await client.get(f"{SHARED}/{code}")).json(),
        asha,
        await _start(client, code, asha),
        (await client.get(f"{SHARED}/{code}/me", headers=_tok(asha))).json(),
        (await client.post(f"{SHARED}/{code}/me/plan/submit", json={}, headers=_tok(asha))).json(),
        (await client.post(f"{SHARED}/{code}/session", json={"device_secret": asha["device_secret"]})).json(),
        ravi,
    ]
    forbidden_keys = {"user_id", "email", "google_email", "google_sub", "secret_hash", "trip_id", "share_id", "owner_id", "notes_private", "allowed_emails"}
    for body in bodies:
        assert not (_all_keys(body) & forbidden_keys), _all_keys(body) & forbidden_keys
        text = json.dumps(body)
        assert "pub17@example.com" not in text and "door code" not in text
    for body in bodies[1:6]:  # what Asha sees never mentions Ravi
        assert "ravi" not in json.dumps(body).lower()
    assert share["id"] not in json.dumps(bodies[0])


# ---- adding places: the owner's quota, links -----------------------------------------------------


@pytest.mark.asyncio
async def test_guest_search_uses_the_owners_key_and_has_its_own_cap(client, google, monkeypatch):
    h, _, share = await _setup(client, "pub18@example.com")
    await _connect_google(client, h)
    code = share["code"]
    joined = await _join(client, code)
    monkeypatch.setattr(shared_plan_service, "_lookups_per_share", shared_plan_service.SlidingWindowLimiter(limit=2, window_seconds=3600))
    url = f"{SHARED}/{code}/maps/autocomplete?q=manali&session=abcdefgh1"
    first = (await client.get(url, headers=_tok(joined))).json()
    assert first["suggestions"][0]["primary"] == "Manali"
    details = (await client.get(f"{SHARED}/{code}/maps/place/ChIJmanali?session=abcdefgh1", headers=_tok(joined))).json()
    assert details["result"]["lat"] == pytest.approx(32.2432)
    capped = (await client.get(url, headers=_tok(joined))).json()
    assert capped == {"suggestions": [], "fallback_reason": "guest_limit"}
    events = await rows(client, MapsUsageEvent)
    assert len(events) == 2 and {e.feature for e in events} == {"shared_search"}
    [owner] = await rows(client, User, email="pub18@example.com")
    assert {e.user_id for e in events} == {owner.id}
    assert (await client.get(url)).status_code == 401  # viewers who have not joined cannot search


@pytest.mark.asyncio
async def test_pasted_links_are_read_without_google_and_short_links_stay_on_google(client, monkeypatch):
    _, _, share = await _setup(client, "pub19@example.com")
    code = share["code"]
    joined = await _join(client, code)
    hops: list[str] = []

    def transport(request: httpx.Request) -> httpx.Response:
        hops.append(str(request.url))
        if request.url.path == "/good":
            return httpx.Response(302, headers={"location": "https://www.google.com/maps/place/Kaza/@32.2276,78.071,15z"})
        if request.url.path == "/metadata":
            return httpx.Response(302, headers={"location": "http://169.254.169.254/latest/meta-data"})
        if request.url.path == "/evil":
            return httpx.Response(301, headers={"location": "https://evil.example.com/maps"})
        return httpx.Response(200, text="<html>no redirect</html>")

    real = httpx.AsyncClient
    monkeypatch.setattr(maps_links, "_http_client", lambda timeout: real(timeout=timeout, transport=httpx.MockTransport(transport)))

    async def resolve(link: str) -> dict:
        resp = await client.get(f"{SHARED}/{code}/resolve-link", params={"url": link}, headers=_tok(joined))
        assert resp.status_code == 200
        return resp.json()

    full = await resolve("https://www.google.com/maps/place/Hampta+Pass/@32.2667,77.3667,14z/data=!3d32.27!4d77.37")
    assert full == {"name": "Hampta Pass", "lat": 32.27, "lng": 77.37, "google_place_id": None}
    assert hops == []  # full links never touch the network
    assert (await resolve("https://maps.app.goo.gl/good"))["name"] == "Kaza"
    empty = {"name": None, "lat": None, "lng": None, "google_place_id": None}
    assert await resolve("https://maps.app.goo.gl/metadata") == empty
    assert await resolve("https://maps.app.goo.gl/evil") == empty
    assert await resolve("https://maps.app.goo.gl/plain") == empty
    assert await resolve("https://evil.example.com/maps/@1,2,3z") == empty
    assert all(h.startswith("https://maps.app.goo.gl/") for h in hops)


# ---- rate limits --------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_joins_are_rate_limited_per_visitor(client):
    _, _, share = await _setup(client, "pub20@example.com")
    for i in range(10):
        await _join(client, share["code"], f"F{i}")
    assert (await client.post(f"{SHARED}/{share['code']}/join/name", json={"name": "F10"})).status_code == 429


# ---- the /t/<code> page -------------------------------------------------------------------------


@pytest.fixture
def index_html(tmp_path, monkeypatch):
    page = tmp_path / "index.html"
    page.write_text(
        '<!doctype html><html><head><title>LifeOS</title>'
        '<link rel="stylesheet" href="styles-X.css" media="print" onload="this.media=\'all\'">'
        "</head><body><app-root></app-root></body></html>"
    )
    monkeypatch.setattr(share_page, "INDEX_HTML", page)
    return page


@pytest.mark.asyncio
async def test_page_has_a_safe_preview_and_strict_headers(client, index_html):
    h, tid, share = await _setup(client, "pub21@example.com")
    await client.patch(f"{BASE}/trips/{tid}", json={"name": 'Goa <script>alert("x")</script>'}, headers=h)
    resp = await client.get(f"/t/{share['code']}")
    assert resp.status_code == 200
    html = resp.text
    assert "<title>Goa &lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;</title>" in html
    assert '<meta property="og:title" content="Goa &lt;script&gt;' in html and "<script>alert" not in html
    assert 'og:image" content="http://test/planner/og-image.png"' in html
    assert "door code" not in html and "onload" not in html
    assert resp.headers["referrer-policy"] == "no-referrer"
    assert resp.headers["x-robots-tag"] == "noindex, nofollow" and resp.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in resp.headers["content-security-policy"]
    assert "https://accounts.google.com/gsi/client" in resp.headers["content-security-policy"]

    await client.post(f"{BASE}/trips/{tid}/share/revoke", headers=h)
    assert "<title>A trip plan</title>" in (await client.get(f"/t/{share['code']}")).text
    assert "<title>A trip plan</title>" in (await client.get("/t/abcdefgh")).text


@pytest.mark.asyncio
async def test_share_versions_table_stays_clean_after_failed_writes(client):
    _, _, share = await _setup(client, "pub22@example.com")
    joined = await _join(client, share["code"])
    await _start(client, share["code"], joined)
    await _save(client, share["code"], joined, {"days": [{"stops": [{"id": "x", "title": ""}]}]}, 1)
    [plan] = [v for v in await rows(client, TravelShareVersion) if v.kind == "plan"]
    assert plan.revision == 1
