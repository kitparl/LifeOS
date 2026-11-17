"""FreeNewsAPI BYOK integration: encrypted key storage, masking, connection test, key resolution for News.
Vendor HTTP is mocked (see the `fake_news` fixture in conftest.py)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.modules.integrations.models import IntegrationConnection
from app.tests.conftest import NEWS_SERVER_KEY
from sqlalchemy import select

API = "/api/v1"
KEY = "freenews-secret-key-1234"
KEY2 = "freenews-second-key-5678"


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
    assert [(k["masked"], k["state"]) for k in body["keys"]] == [("****1234", "ok")]
    assert KEY not in res.text

    stored = await _stored_config(client)
    assert KEY not in stored
    assert len(json.loads(stored)["keys_enc"]) == 1


async def test_keys_are_added_in_order_deduped_capped_and_removable(client):
    h = await _auth(client, "fnkeys@example.com")
    url = f"{API}/integrations/freenewsapi/config"
    await client.put(url, headers=h, json={"api_key": KEY})
    await client.put(url, headers=h, json={"api_key": KEY2})
    dup = await client.put(url, headers=h, json={"api_key": KEY})
    assert [k["masked"] for k in dup.json()["keys"]] == ["****1234", "****5678"]

    for i in range(3):
        assert (await client.put(url, headers=h, json={"api_key": f"extra-key-{i}-000{i}"})).status_code == 200
    over = await client.put(url, headers=h, json={"api_key": "one-key-too-many-9999"})
    assert over.status_code == 400

    first = (await client.get(f"{API}/integrations/freenewsapi", headers=h)).json()["keys"][0]
    removed = await client.delete(f"{API}/integrations/freenewsapi/keys/{first['id']}", headers=h)
    assert removed.status_code == 200
    assert [k["masked"] for k in removed.json()["keys"]][0] == "****5678"
    assert len(removed.json()["keys"]) == 4
    assert (await client.delete(f"{API}/integrations/freenewsapi/keys/nope", headers=h)).status_code == 404


async def test_a_legacy_single_key_config_still_works(client, fake_news):
    from app.core.crypto import encrypt

    h = await _auth(client, "fnlegacy@example.com")
    await client.put(f"{API}/integrations/freenewsapi/config", headers=h, json={"api_key": "placeholder-0000"})
    async with client.session_factory() as db:
        conn = (await db.execute(select(IntegrationConnection))).scalars().one()
        conn.config_json = json.dumps({"api_key_enc": encrypt(KEY)})
        await db.commit()
    status = (await client.get(f"{API}/integrations/freenewsapi", headers=h)).json()
    assert [k["masked"] for k in status["keys"]] == ["****1234"]
    await client.get(f"{API}/news/articles?q=legacy", headers=h)
    assert fake_news.keys_used()[0] == KEY


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
    assert "****1234" in body["detail"]
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


async def test_news_fails_over_to_the_next_key_and_status_shows_the_exhausted_one(client, fake_news):
    h = await _auth(client, "fnfail@example.com")
    url = f"{API}/integrations/freenewsapi/config"
    await client.put(url, headers=h, json={"api_key": KEY})
    await client.put(url, headers=h, json={"api_key": KEY2})
    fake_news.key_responses[KEY] = (402, {}, {"detail": "quota used up", "renews_at": "2999-01-01T00:00:00Z"})

    res = await client.get(f"{API}/news/articles?q=failover", headers=h)
    assert res.status_code == 200
    assert fake_news.keys_used() == [KEY, KEY2]

    keys = (await client.get(f"{API}/integrations/freenewsapi", headers=h)).json()["keys"]
    assert [(k["masked"], k["state"]) for k in keys] == [("****1234", "quota_exhausted"), ("****5678", "ok")]
    assert keys[0]["retry_at"].startswith("2999-01-01")


async def test_when_every_key_is_exhausted_news_reports_quota_exhausted(client, fake_news, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "freenews_api_key", "")
    h = await _auth(client, "fnall@example.com")
    await client.put(f"{API}/integrations/freenewsapi/config", headers=h, json={"api_key": KEY})
    fake_news.status = 402
    res = await client.get(f"{API}/news/articles?q=allout", headers=h)
    assert res.status_code == 503
    assert res.json()["detail"]["code"] == "quota_exhausted"


async def test_test_connection_checks_every_key_and_reports_the_failing_one(client, fake_news):
    h = await _auth(client, "fnmulti@example.com")
    url = f"{API}/integrations/freenewsapi/config"
    await client.put(url, headers=h, json={"api_key": KEY})
    await client.put(url, headers=h, json={"api_key": KEY2})
    fake_news.key_responses[KEY] = (402, {}, {"detail": "quota"})

    body = (await client.post(f"{API}/integrations/freenewsapi/test", headers=h)).json()
    assert body["ok"] is True
    assert body["detail"].startswith("1 of 2 keys working.")
    assert "****1234" in body["detail"]

    del fake_news.key_responses[KEY]  # a re-test re-evaluates keys that were parked
    body = (await client.post(f"{API}/integrations/freenewsapi/test", headers=h)).json()
    assert body == {"ok": True, "detail": "All 2 keys verified"}


async def test_status_shows_each_keys_remaining_quota_after_a_test(client, fake_news):
    h = await _auth(client, "fnquota@example.com")
    url = f"{API}/integrations/freenewsapi/config"
    await client.put(url, headers=h, json={"api_key": KEY})
    await client.put(url, headers=h, json={"api_key": KEY2})
    before = (await client.get(f"{API}/integrations/freenewsapi", headers=h)).json()["keys"]
    assert all(k["quota_remaining"] is None for k in before)  # unknown until a key is used

    fake_news.key_responses[KEY2] = (200, {"X-Quota-Limit": "3000", "X-Quota-Remaining": "12"}, fake_news.search)
    await client.post(f"{API}/integrations/freenewsapi/test", headers=h)
    keys = (await client.get(f"{API}/integrations/freenewsapi", headers=h)).json()["keys"]
    assert [(k["quota_remaining"], k["quota_limit"]) for k in keys] == [(2500, 3000), (12, 3000)]
    renews = datetime.fromisoformat(keys[0]["quota_renews_at"])
    assert renews.day == 1 and renews.hour == 0 and renews > datetime.now(timezone.utc)


async def test_a_single_key_can_be_tested_on_its_own(client, fake_news):
    h = await _auth(client, "fnone@example.com")
    url = f"{API}/integrations/freenewsapi/config"
    await client.put(url, headers=h, json={"api_key": KEY})
    await client.put(url, headers=h, json={"api_key": KEY2})
    keys = (await client.get(f"{API}/integrations/freenewsapi", headers=h)).json()["keys"]
    fake_news.key_responses[KEY] = (402, {}, {"detail": "quota"})

    bad = (await client.post(f"{API}/integrations/freenewsapi/keys/{keys[0]['id']}/test", headers=h)).json()
    assert bad["ok"] is False and bad["detail"].startswith("****1234:")
    good = (await client.post(f"{API}/integrations/freenewsapi/keys/{keys[1]['id']}/test", headers=h)).json()
    assert good == {"ok": True, "detail": "****5678 is active · 2,500 of 3,000 requests left"}
    assert fake_news.keys_used() == [KEY, KEY2]  # only the tested key is called each time

    missing = await client.post(f"{API}/integrations/freenewsapi/keys/nope/test", headers=h)
    assert missing.status_code == 404
    other = await _auth(client, "fnone2@example.com")
    foreign = await client.post(f"{API}/integrations/freenewsapi/keys/{keys[0]['id']}/test", headers=other)
    assert foreign.status_code == 404


async def test_a_quota_reading_from_an_earlier_month_is_ignored(fake_news):
    from app.modules.news import key_pool

    key_pool.record_quota(KEY, 5, 3000)
    assert key_pool.quota(KEY) is not None
    key_pool._quotas[key_pool.fingerprint(KEY)] = key_pool.KeyQuota(
        remaining=5, limit=3000, observed_at=key_pool.month_start(datetime.now(timezone.utc)) - timedelta(seconds=1)
    )
    assert key_pool.quota(KEY) is None
