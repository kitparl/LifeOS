"""FreeNewsAPI BYOK integration: encrypted key storage, masking, connection test, key resolution for News.
Vendor HTTP is mocked (see the `fake_news` fixture in conftest.py)."""

from __future__ import annotations

import json

from app.modules.integrations.models import IntegrationConnection
from app.tests.conftest import NEWS_SERVER_KEY
from sqlalchemy import select

API = "/api/v1"
KEY = "freenews-secret-key-1234"


async def _auth(client, email: str) -> dict[str, str]:
    reg = await client.post(
        f"{API}/auth/register",
        json={
            "username": "usr_" + email.split("@")[0].replace(".", "")[:26],
            "email": email,
            "password": "password123",
            "display_name": "News",
        },
    )
    assert reg.status_code in (200, 201), reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


async def _stored_config(client) -> str | None:
    async with client.session_factory() as db:
        conn = (
            await db.execute(select(IntegrationConnection).where(IntegrationConnection.provider == "freenewsapi"))
        ).scalar_one()
        return conn.config_json


async def test_provider_is_listed_in_the_news_group(client):
    res = await client.get(f"{API}/integrations/providers")
    provider = next(p for p in res.json() if p["provider"] == "freenewsapi")
    assert provider["group"] == "news"


async def test_save_masks_key_and_enables(client):
    h = await _auth(client, "fnsave@example.com")
    res = await client.put(f"{API}/integrations/freenewsapi/config", headers=h, json={"api_key": KEY})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["configured"] is True and body["enabled"] is True
    assert body["api_key_masked"] == "****1234"
    assert KEY not in res.text

    stored = await _stored_config(client)
    assert KEY not in stored
    assert "api_key_enc" in json.loads(stored)


async def test_save_with_no_fields_is_rejected(client):
    h = await _auth(client, "fnempty@example.com")
    res = await client.put(f"{API}/integrations/freenewsapi/config", headers=h, json={})
    assert res.status_code == 400


async def test_test_connection_success_records_status(client, fake_news):
    h = await _auth(client, "fntest@example.com")
    await client.put(f"{API}/integrations/freenewsapi/config", headers=h, json={"api_key": KEY})

    res = await client.post(f"{API}/integrations/freenewsapi/test", headers=h)
    assert res.json()["ok"] is True
    assert fake_news.requests[0].headers["Authorization"] == f"Bearer {KEY}"

    status = (await client.get(f"{API}/integrations/freenewsapi", headers=h)).json()
    assert status["last_test_ok"] is True and status["last_tested_at"] is not None


async def test_test_connection_with_bad_key_fails_without_leaking(client, fake_news):
    h = await _auth(client, "fnbad@example.com")
    await client.put(f"{API}/integrations/freenewsapi/config", headers=h, json={"api_key": KEY})
    fake_news.status = 401

    body = (await client.post(f"{API}/integrations/freenewsapi/test", headers=h)).json()
    assert body["ok"] is False
    assert KEY not in body["detail"]
    status = (await client.get(f"{API}/integrations/freenewsapi", headers=h)).json()
    assert status["last_test_ok"] is False


async def test_test_without_key_reports_not_configured(client, fake_news):
    h = await _auth(client, "fnnokey@example.com")
    res = await client.post(f"{API}/integrations/freenewsapi/test", headers=h)
    assert res.json() == {"ok": False, "detail": "FreeNewsAPI key not configured"}
    assert fake_news.requests == []


async def test_news_uses_the_users_key_then_the_server_fallback(client, fake_news):
    h = await _auth(client, "fnuse@example.com")
    await client.get(f"{API}/news/articles?q=one", headers=h)
    assert fake_news.requests[-1].headers["Authorization"] == f"Bearer {NEWS_SERVER_KEY}"

    await client.put(f"{API}/integrations/freenewsapi/config", headers=h, json={"api_key": KEY})
    await client.get(f"{API}/news/articles?q=two", headers=h)
    assert fake_news.requests[-1].headers["Authorization"] == f"Bearer {KEY}"

    await client.put(f"{API}/integrations/freenewsapi/config", headers=h, json={"enabled": False})
    await client.get(f"{API}/news/articles?q=three", headers=h)
    assert fake_news.requests[-1].headers["Authorization"] == f"Bearer {NEWS_SERVER_KEY}"


async def test_news_without_any_key_reports_missing_credential(client, fake_news, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "freenews_api_key", "")
    res = await client.get(f"{API}/news/articles?q=none")
    assert res.status_code == 503
    assert res.json()["detail"]["code"] == "missing_credential"
    assert fake_news.requests == []
