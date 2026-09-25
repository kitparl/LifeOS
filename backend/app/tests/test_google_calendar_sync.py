"""Google Calendar integration: config, mapping, import, read-only guard, two-way push, disconnect.

All Google HTTP is mocked (token endpoint + Calendar API) — no network.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import get_settings
from app.modules.integrations.google_calendar import oauth
from app.modules.integrations.google_calendar import sync_service as gsync
from app.modules.integrations.google_calendar.client import GoogleCalendarClient, GoogleCalendarClientError
from app.modules.integrations.google_calendar.config import (
    SCOPE_READONLY,
    SCOPE_READWRITE,
    parse_config,
    serialize_config,
)
from app.modules.integrations.google_calendar.mapping import map_google_event, to_google_patch

API = "/api/v1"


# ── pure helpers ──────────────────────────────────────────────────────────────


def test_config_round_trip_encrypts_refresh_token():
    raw = serialize_config(None, refresh_token="1//secret-refresh", scope=SCOPE_READONLY)
    assert "1//secret-refresh" not in raw
    cfg = parse_config(raw)
    assert cfg.refresh_token == "1//secret-refresh"
    assert cfg.sync_direction == "google_to_lifeos"
    assert cfg.calendar_id == "primary"
    assert cfg.can_write is False


def test_config_can_write_needs_exact_scope_and_rejects_bad_direction():
    cfg = parse_config(serialize_config(None, refresh_token="t", scope=SCOPE_READWRITE, sync_direction="bogus"))
    assert cfg.can_write is True
    assert cfg.sync_direction == "google_to_lifeos"


def test_config_tampered_token_fails_closed():
    raw = json.dumps({"refresh_token_enc": "not-a-fernet-token", "scope": SCOPE_READWRITE})
    assert parse_config(raw).connected is False


def test_map_timed_event():
    m = map_google_event(
        {
            "id": "abc123",
            "summary": "Standup",
            "location": "Room 1",
            "start": {"dateTime": "2026-09-24T09:00:00+05:30"},
            "end": {"dateTime": "2026-09-24T09:30:00+05:30"},
        },
        "Asia/Kolkata",
    )
    assert m.all_day is False
    assert m.starts_at == datetime(2026, 9, 24, 3, 30, tzinfo=timezone.utc)
    assert m.ends_at - m.starts_at == timedelta(minutes=30)


def test_map_all_day_event_uses_calendar_tz_and_inclusive_end():
    m = map_google_event(
        {"id": "d1", "start": {"date": "2026-09-24"}, "end": {"date": "2026-09-26"}}, "Asia/Kolkata"
    )
    assert m.all_day is True
    assert m.title == "(No title)"
    # local midnight IST = 18:30 UTC previous day
    assert m.starts_at == datetime(2026, 9, 23, 18, 30, tzinfo=timezone.utc)
    # exclusive end 26th -> last day 25th 23:59:59 IST
    assert m.ends_at == datetime(2026, 9, 25, 18, 29, 59, tzinfo=timezone.utc)


def test_map_skips_cancelled_and_oversized_ids():
    assert map_google_event({"id": "x", "status": "cancelled", "start": {"date": "2026-01-01"}}, None) is None
    assert map_google_event({"id": "x" * 300, "start": {"date": "2026-01-01"}}, None) is None
    assert map_google_event({"id": "x"}, None) is None


def test_to_google_patch_all_day_round_trip():
    m = map_google_event({"id": "d1", "start": {"date": "2026-09-24"}, "end": {"date": "2026-09-25"}}, "Asia/Kolkata")
    body = to_google_patch(
        title="T", description=None, location=None, starts_at=m.starts_at, ends_at=m.ends_at,
        all_day=True, calendar_tz="Asia/Kolkata",
    )
    assert body["start"]["date"] == "2026-09-24"
    assert body["end"]["date"] == "2026-09-25"


def test_state_bound_to_user():
    state = oauth.create_state("user-a", "two_way")
    assert oauth.verify_state(state, "user-a") == "two_way"
    with pytest.raises(oauth.GoogleOAuthError):
        oauth.verify_state(state, "user-b")
    with pytest.raises(oauth.GoogleOAuthError):
        oauth.verify_state("garbage", "user-a")


# ── API-level fixtures ────────────────────────────────────────────────────────


def _gevent(eid: str, title: str, start: datetime, **extra) -> dict:
    return {
        "id": eid,
        "summary": title,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": (start + timedelta(hours=1)).isoformat()},
        **extra,
    }


class FakeGoogle:
    """Stands in for the token endpoint and Calendar API."""

    def __init__(self):
        self.events: list[dict] = []
        self.patched: list[tuple[str, dict]] = []
        self.deleted: list[str] = []
        self.revoked: list[str] = []
        self.list_error = False
        self.scope = SCOPE_READONLY


@pytest.fixture
def fake_google(monkeypatch):
    fg = FakeGoogle()

    async def exchange_code(code):
        return "refresh-tok-" + code, fg.scope

    async def refresh_access_token(refresh):
        return "access-tok"

    async def revoke(token):
        fg.revoked.append(token)

    async def list_events(self, time_min, time_max):
        if fg.list_error:
            raise GoogleCalendarClientError("boom", status_code=500)
        return list(fg.events), "UTC"

    async def patch_event(self, event_id, body):
        fg.patched.append((event_id, body))

    async def delete_event(self, event_id):
        fg.deleted.append(event_id)

    monkeypatch.setattr(oauth, "exchange_code", exchange_code)
    monkeypatch.setattr(oauth, "refresh_access_token", refresh_access_token)
    monkeypatch.setattr(oauth, "revoke", revoke)
    monkeypatch.setattr(GoogleCalendarClient, "list_events", list_events)
    monkeypatch.setattr(GoogleCalendarClient, "patch_event", patch_event)
    monkeypatch.setattr(GoogleCalendarClient, "delete_event", delete_event)
    gsync._last_manual_sync.clear()
    return fg


async def _login(client, email="gcal@example.com"):
    reg = await client.post(
        f"{API}/auth/register",
        json={"username": "usr_" + email.split("@")[0], "email": email, "password": "password123", "display_name": "G"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    me = await client.get(f"{API}/auth/me", headers=headers)
    return headers, me.json()["id"]


async def _connect(client, headers, user_id, mode="google_to_lifeos"):
    res = await client.post(
        f"{API}/integrations/google-calendar/oauth/callback",
        headers=headers,
        json={"code": "c1", "state": oauth.create_state(user_id, mode)},
    )
    assert res.status_code == 200, res.text
    return res.json()


async def _events(client, headers):
    now = datetime.now(timezone.utc)
    res = await client.get(
        f"{API}/calendar/events",
        headers=headers,
        params={"start": (now - timedelta(days=40)).isoformat(), "end": (now + timedelta(days=100)).isoformat(), "limit": 100},
    )
    assert res.status_code == 200
    return res.json()


# ── import ────────────────────────────────────────────────────────────────────


async def test_connect_imports_and_resync_is_idempotent(client, fake_google):
    headers, uid = await _login(client)
    soon = datetime.now(timezone.utc) + timedelta(days=2)
    fake_google.events = [_gevent("g1", "Dentist", soon), _gevent("g2", "Gym", soon + timedelta(days=1))]

    status = await _connect(client, headers, uid)
    assert status["configured"] is True and status["enabled"] is True
    assert status["last_sync_ok"] is True
    assert "refresh" not in json.dumps(status)  # never leak tokens

    items = await _events(client, headers)
    assert sorted(e["title"] for e in items) == ["Dentist", "Gym"]
    assert all(e["source_module"] == "google_calendar" and e["read_only"] for e in items)

    gsync._last_manual_sync.clear()
    res = await client.post(f"{API}/integrations/google-calendar/sync", headers=headers)
    assert res.status_code == 200 and res.json()["status"] == "synced"
    assert len(await _events(client, headers)) == 2


async def test_sync_updates_and_removes_vanished_but_keeps_local_events(client, fake_google):
    headers, uid = await _login(client)
    soon = datetime.now(timezone.utc) + timedelta(days=2)
    local = await client.post(
        f"{API}/calendar/events", headers=headers, json={"title": "Local only", "starts_at": soon.isoformat()}
    )
    assert local.status_code == 201
    fake_google.events = [_gevent("g1", "Old title", soon), _gevent("g2", "Will vanish", soon)]
    await _connect(client, headers, uid)

    fake_google.events = [_gevent("g1", "New title", soon)]
    gsync._last_manual_sync.clear()
    res = await client.post(f"{API}/integrations/google-calendar/sync", headers=headers)
    assert "removed 1" in res.json()["message"]

    titles = sorted(e["title"] for e in await _events(client, headers))
    assert titles == ["Local only", "New title"]


async def test_fetch_failure_does_not_delete_local_copies(client, fake_google):
    headers, uid = await _login(client)
    fake_google.events = [_gevent("g1", "Keep me", datetime.now(timezone.utc) + timedelta(days=1))]
    await _connect(client, headers, uid)

    fake_google.list_error = True
    gsync._last_manual_sync.clear()
    res = await client.post(f"{API}/integrations/google-calendar/sync", headers=headers)
    assert res.json()["status"] == "error"
    assert [e["title"] for e in await _events(client, headers)] == ["Keep me"]
    status = (await client.get(f"{API}/integrations/google-calendar", headers=headers)).json()
    assert status["status"] == "error" and status["last_sync_ok"] is False


async def test_manual_sync_cooldown(client, fake_google):
    headers, uid = await _login(client)
    await _connect(client, headers, uid)
    assert (await client.post(f"{API}/integrations/google-calendar/sync", headers=headers)).status_code == 200
    assert (await client.post(f"{API}/integrations/google-calendar/sync", headers=headers)).status_code == 429


async def test_oauth_callback_rejects_state_for_other_user(client, fake_google):
    headers, _uid = await _login(client)
    res = await client.post(
        f"{API}/integrations/google-calendar/oauth/callback",
        headers=headers,
        json={"code": "c1", "state": oauth.create_state("someone-else", "google_to_lifeos")},
    )
    assert res.status_code == 400


async def test_oauth_start_requires_server_config(client, fake_google, monkeypatch):
    headers, _uid = await _login(client)
    res = await client.get(f"{API}/integrations/google-calendar/oauth/start", headers=headers)
    assert res.status_code == 503

    s = get_settings()
    monkeypatch.setattr(s, "google_client_id", "cid.apps.googleusercontent.com")
    monkeypatch.setattr(s, "google_client_secret", "sec")
    monkeypatch.setattr(s, "google_calendar_redirect_uri", "http://localhost:4200/integrations")
    res = await client.get(
        f"{API}/integrations/google-calendar/oauth/start", headers=headers, params={"mode": "two_way"}
    )
    assert res.status_code == 200
    url = res.json()["auth_url"]
    assert "calendar.events" in url and "readonly" not in url and "access_type=offline" in url


async def test_generic_endpoints_never_expose_or_accept_config(client, fake_google):
    headers, uid = await _login(client)
    await _connect(client, headers, uid)
    listing = (await client.get(f"{API}/integrations", headers=headers)).json()
    gc = next(c for c in listing if c["provider"] == "google_calendar")
    assert gc["config_json"] is None
    await client.patch(
        f"{API}/integrations/{gc['id']}", headers=headers, json={"config_json": '{"scope": "x"}'}
    )
    status = (await client.get(f"{API}/integrations/google-calendar", headers=headers)).json()
    assert status["configured"] is True


# ── read-only / two-way ───────────────────────────────────────────────────────


async def test_one_way_rejects_edit_and_delete_and_never_writes_google(client, fake_google):
    headers, uid = await _login(client)
    fake_google.events = [_gevent("g1", "Imported", datetime.now(timezone.utc) + timedelta(days=1))]
    await _connect(client, headers, uid)
    ev = (await _events(client, headers))[0]

    assert (await client.patch(f"{API}/calendar/events/{ev['id']}", headers=headers, json={"title": "x"})).status_code == 400
    assert (await client.delete(f"{API}/calendar/events/{ev['id']}", headers=headers)).status_code == 400
    assert fake_google.patched == [] and fake_google.deleted == []


async def test_two_way_without_write_scope_stays_read_only(client, fake_google):
    headers, uid = await _login(client)
    fake_google.events = [_gevent("g1", "Imported", datetime.now(timezone.utc) + timedelta(days=1))]
    await _connect(client, headers, uid)  # read-only grant
    status = (
        await client.put(f"{API}/integrations/google-calendar/config", headers=headers, json={"sync_direction": "two_way"})
    ).json()
    assert status["sync_direction"] == "two_way" and status["can_write"] is False
    ev = (await _events(client, headers))[0]
    assert ev["read_only"] is True
    assert (await client.patch(f"{API}/calendar/events/{ev['id']}", headers=headers, json={"title": "x"})).status_code == 400


async def test_two_way_pushes_linked_edits_and_deletes_only(client, fake_google):
    headers, uid = await _login(client)
    fake_google.scope = SCOPE_READWRITE
    soon = datetime.now(timezone.utc) + timedelta(days=1)
    fake_google.events = [_gevent("g1", "Imported", soon), _gevent("g2", "Second", soon)]
    await _connect(client, headers, uid, mode="two_way")
    local = await client.post(f"{API}/calendar/events", headers=headers, json={"title": "Local", "starts_at": soon.isoformat()})

    by_title = {e["title"]: e for e in await _events(client, headers)}
    assert by_title["Imported"]["read_only"] is False

    res = await client.patch(f"{API}/calendar/events/{by_title['Imported']['id']}", headers=headers, json={"title": "Renamed"})
    assert res.status_code == 200 and res.json()["title"] == "Renamed"
    assert fake_google.patched[0][0] == "g1" and fake_google.patched[0][1]["summary"] == "Renamed"

    assert (await client.patch(
        f"{API}/calendar/events/{by_title['Imported']['id']}", headers=headers, json={"recurrence": "weekly"}
    )).status_code == 400

    assert (await client.delete(f"{API}/calendar/events/{by_title['Second']['id']}", headers=headers)).status_code == 204
    assert fake_google.deleted == ["g2"]

    # LifeOS-native events never reach Google
    await client.patch(f"{API}/calendar/events/{local.json()['id']}", headers=headers, json={"title": "Local 2"})
    assert len(fake_google.patched) == 1

    # Switching back to one-way stops writes immediately
    await client.put(f"{API}/integrations/google-calendar/config", headers=headers, json={"sync_direction": "google_to_lifeos"})
    assert (await client.patch(
        f"{API}/calendar/events/{by_title['Imported']['id']}", headers=headers, json={"title": "Again"}
    )).status_code == 400
    assert len(fake_google.patched) == 1


async def test_two_way_google_failure_rolls_back_local_edit(client, fake_google, monkeypatch):
    headers, uid = await _login(client)
    fake_google.scope = SCOPE_READWRITE
    fake_google.events = [_gevent("g1", "Imported", datetime.now(timezone.utc) + timedelta(days=1))]
    await _connect(client, headers, uid, mode="two_way")

    async def failing_patch(self, event_id, body):
        raise GoogleCalendarClientError("nope", status_code=500)

    monkeypatch.setattr(GoogleCalendarClient, "patch_event", failing_patch)
    ev = (await _events(client, headers))[0]
    res = await client.patch(f"{API}/calendar/events/{ev['id']}", headers=headers, json={"title": "Renamed"})
    assert res.status_code == 502
    assert (await _events(client, headers))[0]["title"] == "Imported"


# ── disable / disconnect ──────────────────────────────────────────────────────


async def test_disabled_connection_does_not_sync(client, fake_google):
    headers, uid = await _login(client)
    await _connect(client, headers, uid)
    await client.put(f"{API}/integrations/google-calendar/config", headers=headers, json={"enabled": False})
    gsync._last_manual_sync.clear()
    assert (await client.post(f"{API}/integrations/google-calendar/sync", headers=headers)).status_code == 400


async def test_cannot_enable_without_oauth(client, fake_google):
    headers, _uid = await _login(client)
    created = await client.post(f"{API}/integrations", headers=headers, json={"provider": "google_calendar", "enabled": True})
    assert created.status_code == 201 and created.json()["enabled"] is False
    res = await client.patch(f"{API}/integrations/{created.json()['id']}", headers=headers, json={"enabled": True})
    assert res.status_code == 400


async def test_disconnect_revokes_and_removes_only_google_events(client, fake_google):
    headers, uid = await _login(client)
    soon = datetime.now(timezone.utc) + timedelta(days=1)
    await client.post(f"{API}/calendar/events", headers=headers, json={"title": "Local", "starts_at": soon.isoformat()})
    fake_google.events = [_gevent("g1", "Imported", soon)]
    await _connect(client, headers, uid)

    assert (await client.delete(f"{API}/integrations/google-calendar", headers=headers)).status_code == 204
    assert fake_google.revoked == ["refresh-tok-c1"]
    assert [e["title"] for e in await _events(client, headers)] == ["Local"]
    status = (await client.get(f"{API}/integrations/google-calendar", headers=headers)).json()
    assert status["configured"] is False and status["enabled"] is False


@pytest.mark.parametrize(
    "name,config_path,status_path,body",
    [
        ("github", "github/config", "github", {"token": "ghp_secret1234", "repo": "owner/repo"}),
        ("sarvam", "ai/sarvam/config", "ai/sarvam/config", {"api_key": "sk_secret1234"}),
        ("telegram", "telegram/config", "telegram", {"bot_token": "123:ABC", "chat_id": "42"}),
    ],
)
async def test_generic_patch_config_json_does_not_wipe_secret_config(client, name, config_path, status_path, body):
    """Regression: model_copy(update={"config_json": None}) marked the field set and wiped config."""
    headers, _uid = await _login(client, f"{name}wipe@example.com")
    saved = await client.put(f"{API}/integrations/{config_path}", headers=headers, json=body)
    assert saved.status_code == 200 and saved.json()["configured"] is True
    conn_id = saved.json()["connection_id"]

    res = await client.patch(
        f"{API}/integrations/{conn_id}", headers=headers, json={"config_json": "{}", "display_name": "Renamed"}
    )
    assert res.status_code == 200 and res.json()["display_name"] == "Renamed"
    assert (await client.get(f"{API}/integrations/{status_path}", headers=headers)).json()["configured"] is True
