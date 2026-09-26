"""News proxy endpoints and saved-article library (save, dedupe, expiry, cleanup, isolation, limits)."""

from datetime import UTC, datetime, timedelta

import pytest
from app.core.config import get_settings
from app.modules.news import service as news_service
from app.modules.news.models import NewsCollectionArticle, NewsSavedArticle
from app.modules.news.service import NewsService
from app.tests.conftest import NEWS_RESULT
from sqlalchemy import select, update

URL = NEWS_RESULT["url"]


async def _headers(client, email: str) -> dict[str, str]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "usr_" + email.split("@")[0].replace(".", "")[:26],
            "email": email,
            "password": "password123",
            "display_name": "News User",
        },
    )
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


def _snapshot(url: str = URL, title: str = "AI centre proposal") -> dict:
    return {
        "article_external_id": "a1",
        "article_url": url,
        "title": title,
        "description": None,
        "image": None,
        "publisher": "The Hindu",
        "host": "www.thehindu.com",
        "author": None,
        "published_at": "2026-09-25T10:00:00Z",
    }


async def _expire(client, saved_id: str) -> None:
    async with client.session_factory() as session:
        await session.execute(
            update(NewsSavedArticle)
            .where(NewsSavedArticle.id == saved_id)
            .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
        )
        await session.commit()


# ------------------------------------------------------------------ live news proxy


async def test_library_endpoints_require_auth(client):
    for path in ("/api/v1/news/saved", "/api/v1/news/collections", "/api/v1/news/collections/c1/articles"):
        assert (await client.get(path)).status_code == 401
    assert (await client.post("/api/v1/news/saved", json=_snapshot())).status_code == 401
    assert (await client.delete("/api/v1/news/saved/s1")).status_code == 401
    assert (await client.post("/api/v1/news/collections", json={"name": "AI"})).status_code == 401


async def test_live_news_is_public_without_saved_state(client, fake_news):
    """Explore guests browse live news; nothing is annotated from (or written to) the database."""
    owner = await _headers(client, "owner@example.com")
    assert (await client.post("/api/v1/news/saved", headers=owner, json=_snapshot())).status_code == 201

    categories = await client.get("/api/v1/news/categories")
    assert categories.status_code == 200
    articles = await client.get("/api/v1/news/articles", params={"category": "ai"})
    assert articles.status_code == 200
    assert articles.json()["items"][0]["saved_article_id"] is None
    fake_news.article = {**NEWS_RESULT, "text": "P1."}
    detail = await client.get("/api/v1/news/article", params={"url": URL})
    assert detail.status_code == 200
    assert detail.json()["saved_article_id"] is None

    async with client.session_factory() as session:
        assert len((await session.execute(select(NewsSavedArticle))).scalars().all()) == 1


async def test_live_news_rejects_an_invalid_token(client, fake_news):
    res = await client.get("/api/v1/news/articles", headers={"Authorization": "Bearer not-a-jwt"})
    assert res.status_code == 401


async def test_categories_listed(client):
    headers = await _headers(client, "cats@example.com")
    res = await client.get("/api/v1/news/categories", headers=headers)
    assert res.status_code == 200
    assert res.json()[1] == {"id": "ai", "label": "AI"}


async def test_articles_category_maps_to_vendor_params_and_annotates_saved(client, fake_news):
    headers = await _headers(client, "feed@example.com")
    saved = await client.post("/api/v1/news/saved", headers=headers, json=_snapshot())
    res = await client.get(
        "/api/v1/news/articles", headers=headers, params={"category": "ai", "lang": "en", "limit": 10}
    )
    assert res.status_code == 200
    body = res.json()
    assert fake_news.params() == {
        "q": "artificial intelligence", "lang": "en", "sort": "date", "size": "10", "offset": "0"
    }
    assert body["items"][0]["title"] == 'AI centre "proposal" submitted'
    assert body["items"][0]["saved_article_id"] == saved.json()["id"]
    assert body["has_more"] is False


async def test_articles_dedupes_and_uses_backend_cache(client, fake_news):
    headers = await _headers(client, "cache@example.com")
    dup = {**NEWS_RESULT, "id": "a2", "url": URL + "?utm_source=rss"}
    fake_news.search = {"total": 500, "results": [NEWS_RESULT, dup]}
    first = await client.get("/api/v1/news/articles", headers=headers, params={"country": "IN"})
    second = await client.get("/api/v1/news/articles", headers=headers, params={"country": "IN"})
    assert [a["id"] for a in first.json()["items"]] == ["a1"]
    assert first.json()["has_more"] is True
    assert second.json() == first.json()
    assert len(fake_news.requests) == 1


@pytest.mark.parametrize(
    "params",
    [
        {"q": "ai", "category": "ai"},
        {"category": "unknown"},
        {"country": "india"},
        {"lang": "EN"},
        {"host": "not a host"},
        {"date": "1y"},
        {"sort": "popular"},
        {"limit": 51},
        {"offset": 9901},
        {"q": "x" * 201},
    ],
)
async def test_articles_rejects_invalid_params(client, fake_news, params):
    headers = await _headers(client, "invalid@example.com")
    res = await client.get("/api/v1/news/articles", headers=headers, params=params)
    assert res.status_code in (400, 422)
    assert fake_news.requests == []


@pytest.mark.parametrize(("status", "http", "code"), [(429, 429, "rate_limit"), (500, 503, "provider_unavailable")])
async def test_vendor_errors_are_coded(client, fake_news, status, http, code):
    headers = await _headers(client, f"err{status}@example.com")
    fake_news.status = status
    res = await client.get("/api/v1/news/articles", headers=headers)
    assert res.status_code == http
    assert res.json()["detail"]["code"] == code


async def test_vendor_offline_by_default_returns_503(client):
    headers = await _headers(client, "offline@example.com")
    news_service.reset_vendor_state()
    res = await client.get("/api/v1/news/articles", headers=headers, params={"q": "anything"})
    assert res.status_code == 503
    assert res.json()["detail"]["code"] == "provider_unavailable"


async def test_proxy_rate_limit(client, fake_news, monkeypatch):
    monkeypatch.setattr(get_settings(), "news_proxy_per_minute", 2)
    news_service.reset_vendor_state()
    headers = await _headers(client, "limit@example.com")
    for _ in range(2):
        assert (await client.get("/api/v1/news/articles", headers=headers)).status_code == 200
    res = await client.get("/api/v1/news/articles", headers=headers)
    assert res.status_code == 429
    assert res.json()["detail"]["code"] == "rate_limit"


async def test_anonymous_proxy_rate_limit_is_per_client_and_separate_from_users(client, fake_news, monkeypatch):
    monkeypatch.setattr(get_settings(), "news_proxy_per_minute", 2)
    news_service.reset_vendor_state()
    for _ in range(2):
        assert (await client.get("/api/v1/news/articles")).status_code == 200
    res = await client.get("/api/v1/news/article", params={"url": URL})
    assert res.status_code == 429
    assert res.json()["detail"]["code"] == "rate_limit"
    headers = await _headers(client, "notguest@example.com")
    assert (await client.get("/api/v1/news/articles", headers=headers)).status_code == 200


async def test_article_detail_returns_excerpt_only(client, fake_news):
    headers = await _headers(client, "detail@example.com")
    fake_news.article = {**NEWS_RESULT, "text": "P1.\n\nP2.\n\nP3.\n\nP4 should not be returned."}
    res = await client.get("/api/v1/news/article", headers=headers, params={"url": URL})
    assert res.status_code == 200
    body = res.json()
    assert body["excerpt"] == ["P1.", "P2.", "P3."]
    assert "text" not in body
    assert body["saved_article_id"] is None


async def test_article_detail_unavailable_and_url_validation(client, fake_news):
    headers = await _headers(client, "missing@example.com")
    fake_news.article = None
    res = await client.get("/api/v1/news/article", headers=headers, params={"url": "https://example.com/gone"})
    assert res.status_code == 404
    assert res.json()["detail"]["code"] == "article_unavailable"
    bad = await client.get("/api/v1/news/article", headers=headers, params={"url": "file:///etc/passwd"})
    assert bad.status_code == 422


# ------------------------------------------------------------------ saved articles


async def test_save_sets_expiry_from_setting_and_prevents_duplicates(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "article_retention_days", 10)
    headers = await _headers(client, "save@example.com")
    first = await client.post("/api/v1/news/saved", headers=headers, json=_snapshot())
    assert first.status_code == 201
    body = first.json()
    saved_at = datetime.fromisoformat(body["saved_at"])
    expires_at = datetime.fromisoformat(body["expires_at"])
    assert saved_at.tzinfo is not None
    assert expires_at - saved_at == timedelta(days=10)
    assert body["already_saved"] is False

    again = await client.post("/api/v1/news/saved", headers=headers, json=_snapshot(title="Other title"))
    assert again.status_code == 200
    assert again.json()["id"] == body["id"]
    assert again.json()["already_saved"] is True
    listing = await client.get("/api/v1/news/saved", headers=headers)
    assert listing.json()["total"] == 1


async def test_save_validates_snapshot(client):
    headers = await _headers(client, "valid@example.com")
    for payload in (
        {**_snapshot(), "article_url": "javascript:alert(1)"},
        {**_snapshot(), "title": "<script></script>"},
        {**_snapshot(), "title": "x" * 501},
    ):
        assert (await client.post("/api/v1/news/saved", headers=headers, json=payload)).status_code == 422
    res = await client.post(
        "/api/v1/news/saved", headers=headers, json={**_snapshot(), "title": "<b>Bold</b> &amp; plain", "image": "ftp://x"}
    )
    assert res.json()["title"] == "Bold & plain"
    assert res.json()["image"] is None


async def test_expired_article_hidden_purged_and_resavable(client):
    headers = await _headers(client, "expire@example.com")
    saved = (await client.post("/api/v1/news/saved", headers=headers, json=_snapshot())).json()
    collection = (await client.post("/api/v1/news/collections", headers=headers, json={"name": "AI"})).json()
    await client.post(
        f"/api/v1/news/collections/{collection['id']}/articles", headers=headers, json={"saved_article_id": saved["id"]}
    )
    await _expire(client, saved["id"])

    listing = await client.get("/api/v1/news/saved", headers=headers)
    assert listing.json() == {"items": [], "total": 0}
    async with client.session_factory() as session:
        assert (await session.execute(select(NewsSavedArticle))).scalars().all() == []
        assert (await session.execute(select(NewsCollectionArticle))).scalars().all() == []
    collections = await client.get("/api/v1/news/collections", headers=headers)
    assert collections.json()[0]["article_count"] == 0

    again = await client.post("/api/v1/news/saved", headers=headers, json=_snapshot())
    assert again.status_code == 201
    assert again.json()["id"] != saved["id"]


async def test_resave_after_expiry_without_lazy_cleanup(client):
    headers = await _headers(client, "resave@example.com")
    saved = (await client.post("/api/v1/news/saved", headers=headers, json=_snapshot())).json()
    await _expire(client, saved["id"])
    again = await client.post("/api/v1/news/saved", headers=headers, json=_snapshot())
    assert again.status_code == 201
    assert again.json()["already_saved"] is False


async def test_scheduled_purge_removes_saved_and_memberships_keeps_collection(client):
    headers = await _headers(client, "purge@example.com")
    keep = (await client.post("/api/v1/news/saved", headers=headers, json=_snapshot(url=URL + "?k=1"))).json()
    gone = (await client.post("/api/v1/news/saved", headers=headers, json=_snapshot())).json()
    collection = (await client.post("/api/v1/news/collections", headers=headers, json={"name": "Read Later"})).json()
    for saved in (keep, gone):
        await client.post(
            f"/api/v1/news/collections/{collection['id']}/articles",
            headers=headers,
            json={"saved_article_id": saved["id"]},
        )
    await _expire(client, gone["id"])

    async with client.session_factory() as session:
        assert await NewsService(session).purge_expired() == 1
        await session.commit()
        members = (await session.execute(select(NewsCollectionArticle))).scalars().all()
        assert [m.saved_article_id for m in members] == [keep["id"]]

    collections = (await client.get("/api/v1/news/collections", headers=headers)).json()
    assert collections == [{**collections[0], "name": "Read Later", "article_count": 1}]


async def test_saved_filters_and_pagination(client):
    headers = await _headers(client, "filters@example.com")
    ids = []
    for i in range(3):
        res = await client.post("/api/v1/news/saved", headers=headers, json=_snapshot(url=f"{URL}?n={i}"))
        ids.append(res.json()["id"])
    async with client.session_factory() as session:
        now = datetime.now(UTC)
        await session.execute(
            update(NewsSavedArticle)
            .where(NewsSavedArticle.id == ids[0])
            .values(saved_at=now - timedelta(days=28), expires_at=now + timedelta(days=2))
        )
        await session.commit()

    page = await client.get("/api/v1/news/saved", headers=headers, params={"limit": 2, "offset": 0})
    assert page.json()["total"] == 3
    assert [a["id"] for a in page.json()["items"]] == [ids[2], ids[1]]
    recent = await client.get("/api/v1/news/saved", headers=headers, params={"filter": "recent"})
    assert {a["id"] for a in recent.json()["items"]} == {ids[1], ids[2]}
    expiring = await client.get("/api/v1/news/saved", headers=headers, params={"filter": "expiring"})
    assert [a["id"] for a in expiring.json()["items"]] == [ids[0]]


async def test_delete_saved_and_user_isolation(client):
    owner = await _headers(client, "owner@example.com")
    other = await _headers(client, "other@example.com")
    saved = (await client.post("/api/v1/news/saved", headers=owner, json=_snapshot())).json()

    assert (await client.get("/api/v1/news/saved", headers=other)).json()["total"] == 0
    assert (await client.delete(f"/api/v1/news/saved/{saved['id']}", headers=other)).status_code == 404
    # Another user saving the same URL gets their own row.
    theirs = await client.post("/api/v1/news/saved", headers=other, json=_snapshot())
    assert theirs.status_code == 201 and theirs.json()["id"] != saved["id"]

    assert (await client.delete(f"/api/v1/news/saved/{saved['id']}", headers=owner)).status_code == 204
    assert (await client.get("/api/v1/news/saved", headers=owner)).json()["total"] == 0


async def test_write_limit(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "news_writes_per_hour", 2)
    headers = await _headers(client, "writes@example.com")
    assert (await client.post("/api/v1/news/saved", headers=headers, json=_snapshot(url=URL + "?a"))).status_code == 201
    assert (await client.post("/api/v1/news/collections", headers=headers, json={"name": "One"})).status_code == 201
    res = await client.post("/api/v1/news/saved", headers=headers, json=_snapshot(url=URL + "?b"))
    assert res.status_code == 429
    assert res.json()["detail"]["code"] == "write_limit"
    # Re-saving an existing article is not a write.
    assert (await client.post("/api/v1/news/saved", headers=headers, json=_snapshot(url=URL + "?a"))).status_code == 200
