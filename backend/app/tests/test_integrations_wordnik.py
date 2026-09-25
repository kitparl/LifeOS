"""Wordnik BYOK integration: encrypted key storage, masking, connection test, usage %, isolation.
All vendor HTTP is mocked (see the `wordnik` fixture in conftest.py)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from app.modules.integrations.models import IntegrationConnection
from app.modules.integrations.wordnik.config import (
    WordnikUsage,
    load_config,
    serialize_config,
    usage_remaining_pct,
    with_usage,
)
from sqlalchemy import select

API = "/api/v1"
KEY = "wordnik-secret-key-1234"


async def _auth(client, email: str) -> dict[str, str]:
    reg = await client.post(
        f"{API}/auth/register",
        json={
            "username": "usr_" + email.split("@")[0].replace(".", "")[:26],
            "email": email,
            "password": "password123",
            "display_name": "Wordnik",
        },
    )
    assert reg.status_code in (200, 201), reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


async def _stored_config(client, provider: str = "wordnik") -> str | None:
    async with client.session_factory() as db:
        conn = (
            await db.execute(select(IntegrationConnection).where(IntegrationConnection.provider == provider))
        ).scalar_one()
        return conn.config_json


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------


def test_serialize_encrypts_and_blank_key_keeps_existing():
    first = serialize_config(existing_json=None, api_key=KEY)
    assert KEY not in first
    assert load_config(first).api_key == KEY

    kept = serialize_config(existing_json=first, api_key="  ")
    assert load_config(kept).api_key == KEY


def test_new_key_clears_usage_of_the_old_key():
    usage = WordnikUsage(remaining=10, limit=100, observed_at=datetime.now(UTC))
    stored = with_usage(serialize_config(existing_json=None, api_key=KEY), usage)
    assert load_config(stored).usage == usage
    replaced = serialize_config(existing_json=stored, api_key="another-key-9999")
    assert load_config(replaced).usage is None


def test_usage_pct_is_unknown_for_an_earlier_hour_or_zero_limit():
    now = datetime(2026, 9, 25, 10, 30, tzinfo=UTC)
    fresh = WordnikUsage(remaining=73, limit=100, observed_at=now - timedelta(minutes=10))
    stale = WordnikUsage(remaining=73, limit=100, observed_at=now - timedelta(minutes=31))
    assert usage_remaining_pct(fresh, now) == 73
    assert usage_remaining_pct(stale, now) is None
    assert usage_remaining_pct(WordnikUsage(0, 0, now), now) is None
    assert usage_remaining_pct(None, now) is None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


async def test_provider_is_listed_in_the_language_group(client):
    res = await client.get(f"{API}/integrations/providers")
    wordnik = next(p for p in res.json() if p["provider"] == "wordnik")
    assert wordnik["group"] == "language"


async def test_save_masks_key_and_enables(client):
    h = await _auth(client, "wnsave@example.com")
    res = await client.put(f"{API}/integrations/wordnik/config", headers=h, json={"api_key": KEY})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["configured"] is True
    assert body["enabled"] is True
    assert body["api_key_masked"] == "****1234"
    assert KEY not in res.text

    stored = await _stored_config(client)
    assert KEY not in stored
    assert "api_key_enc" in json.loads(stored)


async def test_save_with_no_fields_is_rejected(client):
    h = await _auth(client, "wnempty@example.com")
    res = await client.put(f"{API}/integrations/wordnik/config", headers=h, json={})
    assert res.status_code == 400


async def test_test_connection_success_records_status_and_usage(client, wordnik):
    h = await _auth(client, "wntest@example.com")
    await client.put(f"{API}/integrations/wordnik/config", headers=h, json={"api_key": KEY})

    res = await client.post(f"{API}/integrations/wordnik/test", headers=h)
    assert res.json()["ok"] is True
    assert wordnik.requests[0].headers["api_key"] == KEY
    assert "api_key" not in str(wordnik.requests[0].url)

    status = (await client.get(f"{API}/integrations/wordnik", headers=h)).json()
    assert status["last_test_ok"] is True
    assert status["last_tested_at"] is not None
    assert status["usage_remaining_pct"] == 73


async def test_test_connection_with_bad_key_fails_without_leaking(client, wordnik):
    h = await _auth(client, "wnbad@example.com")
    await client.put(f"{API}/integrations/wordnik/config", headers=h, json={"api_key": KEY})
    wordnik.status = 401

    res = await client.post(f"{API}/integrations/wordnik/test", headers=h)
    body = res.json()
    assert body["ok"] is False
    assert KEY not in body["detail"]
    status = (await client.get(f"{API}/integrations/wordnik", headers=h)).json()
    assert status["last_test_ok"] is False


async def test_test_without_key_reports_not_configured(client, wordnik):
    h = await _auth(client, "wnnokey@example.com")
    res = await client.post(f"{API}/integrations/wordnik/test", headers=h)
    assert res.json() == {"ok": False, "detail": "Wordnik API key not configured"}
    assert wordnik.requests == []


async def test_config_is_isolated_per_user(client):
    alice = await _auth(client, "wnalice@example.com")
    bob = await _auth(client, "wnbob@example.com")
    await client.put(f"{API}/integrations/wordnik/config", headers=alice, json={"api_key": KEY})

    bob_status = (await client.get(f"{API}/integrations/wordnik", headers=bob)).json()
    assert bob_status["configured"] is False
    assert bob_status["api_key_masked"] is None


async def test_generic_patch_cannot_overwrite_the_secret_config(client):
    h = await _auth(client, "wnpatch@example.com")
    status = (await client.put(f"{API}/integrations/wordnik/config", headers=h, json={"api_key": KEY})).json()

    res = await client.patch(
        f"{API}/integrations/{status['connection_id']}", headers=h, json={"config_json": '{"api_key_enc": ""}'}
    )
    assert res.status_code == 200
    assert res.json()["config_json"] is None
    assert load_config(await _stored_config(client)).api_key == KEY
