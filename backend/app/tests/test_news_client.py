"""FreeNewsAPI client, category mapping, de-duplication, excerpt, cache and limiter (no DB)."""

import httpx
import pytest
from app.core.cache import TtlCache
from app.core.rate_limit import SlidingWindowLimiter
from app.modules.news import categories
from app.modules.news.client import FreeNewsClient, NewsApiError, parse_article
from app.modules.news.dedupe import dedupe_articles, normalize_url
from app.modules.news.schemas import NewsArticle
from app.modules.news.service import EXCERPT_MAX_CHARS, build_excerpt
from app.tests.conftest import NEWS_RESULT


def _article(id_: str, url: str, title: str = "Title", host: str | None = None) -> NewsArticle:
    return NewsArticle(id=id_, url=url, title=title, host=host)


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


# ------------------------------------------------------------------ parsing


def test_parse_article_decodes_entities_and_keeps_nulls():
    article = parse_article(NEWS_RESULT)
    assert article is not None
    assert article.title == 'AI centre "proposal" submitted'
    assert article.description is None and article.author is None and article.image is None
    assert article.sitename == "The Hindu"
    assert article.published_at is not None and article.published_at.tzinfo is not None
    assert article.categories == ["technology"]


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "not a dict",
        {**NEWS_RESULT, "url": None},
        {**NEWS_RESULT, "url": "javascript:alert(1)"},
        {**NEWS_RESULT, "title": "   "},
        {**NEWS_RESULT, "title": "<b></b>"},
    ],
)
def test_parse_article_skips_unusable_items(raw):
    assert parse_article(raw) is None


def test_parse_article_rejects_non_http_images_and_bad_fields():
    article = parse_article(
        {**NEWS_RESULT, "image": "data:image/png;base64,xx", "published_at": "garbage", "categories": "tech", "id": None}
    )
    assert article is not None
    assert article.image is None
    assert article.published_at is None
    assert article.categories is None
    assert article.id == article.url  # falls back to the URL as a stable id


# ------------------------------------------------------------------ vendor calls


async def test_search_sends_only_given_params_and_ignores_promo(fake_news):
    fake_news.search = {"total": 1, "results": [NEWS_RESULT], "strongly_recommended": {"x": 1}}
    result = await FreeNewsClient().search({"q": "ai", "size": 5, "offset": 0, "sort": "date"})
    assert fake_news.requests[0].url.host == "freenewsapi.ai"
    assert fake_news.params() == {"q": "ai", "size": "5", "offset": "0", "sort": "date"}
    assert [a.id for a in result.articles] == ["a1"]
    assert result.total == 1


@pytest.mark.parametrize(
    ("status", "code"),
    [(429, "rate_limit"), (500, "provider_unavailable"), (503, "provider_unavailable")],
)
async def test_search_maps_vendor_status_to_codes(fake_news, status, code):
    fake_news.status = status
    with pytest.raises(NewsApiError) as info:
        await FreeNewsClient().search({"q": "ai"})
    assert info.value.code == code


async def test_search_malformed_response(fake_news):
    fake_news.search = {"results": "nope"}
    with pytest.raises(NewsApiError) as info:
        await FreeNewsClient().search({})
    assert info.value.code == "malformed_response"


async def test_timeout_maps_to_timeout_code(monkeypatch):
    from app.modules.news import client as news_client

    def raise_timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    real = httpx.AsyncClient
    monkeypatch.setattr(
        news_client, "_http_client", lambda timeout: real(timeout=timeout, transport=httpx.MockTransport(raise_timeout))
    )
    with pytest.raises(NewsApiError) as info:
        await FreeNewsClient().search({})
    assert info.value.code == "timeout"


async def test_article_404_returns_none_and_body_is_exposed(fake_news):
    found = await FreeNewsClient().article(NEWS_RESULT["url"])
    assert found is not None and found.text == "First paragraph.\n\nSecond paragraph."
    assert fake_news.params() == {"url": NEWS_RESULT["url"], "full_text": "true"}
    fake_news.article = None
    assert await FreeNewsClient().article("https://example.com/missing") is None


# ------------------------------------------------------------------ categories


def test_categories_cover_spec_list_and_resolve_to_documented_params():
    labels = [c.label for c in categories.CATEGORIES]
    assert labels == [
        "All", "AI", "Technology", "Business", "Finance", "Science", "Health",
        "Sports", "Entertainment", "World", "India", "Politics", "Climate", "Startups",
    ]
    assert categories.resolve("all") == {}
    assert categories.resolve("ai") == {"q": "artificial intelligence"}
    assert categories.resolve("india") == {"country": "IN"}
    for c in categories.CATEGORIES:
        assert set(c.params) <= {"q", "country"}
    with pytest.raises(KeyError):
        categories.resolve("nope")


# ------------------------------------------------------------------ de-duplication


def test_normalize_url_drops_noise():
    assert normalize_url("https://WWW.Example.com/a/b/?utm_source=x&id=2&fbclid=z#frag") == "example.com/a/b?id=2"
    assert normalize_url("http://example.com/a/b") == "example.com/a/b"


def test_dedupe_by_id_url_and_same_host_title():
    articles = [
        _article("1", "https://example.com/story", "Big News", "example.com"),
        _article("1", "https://other.com/x", "Different"),  # same id
        _article("2", "https://www.example.com/story/?utm_medium=rss", "Other"),  # same normalized URL
        _article("3", "https://example.com/story-copy", "Big  news!", "www.example.com"),  # same host+title
        _article("4", "https://another.org/story", "Big News", "another.org"),  # same title, different host
    ]
    assert [a.id for a in dedupe_articles(articles)] == ["1", "4"]


# ------------------------------------------------------------------ excerpt


def test_excerpt_takes_first_three_paragraphs_and_strips_truncation_marker():
    text = "One.\n\n  Two <b>bold</b>.\nThree.\n\nFour.\n"
    assert build_excerpt(text) == ["One.", "Two bold.", "Three."]
    assert build_excerpt("Only part… [+2384 chars]") == ["Only part"]
    assert build_excerpt(None) == []


def test_excerpt_is_capped_on_word_boundary():
    excerpt = build_excerpt("word " * 1000)
    assert len(excerpt) == 1
    assert excerpt[0].endswith("…")
    assert len(excerpt[0]) <= EXCERPT_MAX_CHARS + 1


# ------------------------------------------------------------------ cache and limiter


def test_ttl_cache_expiry_and_eviction():
    clock = _Clock()
    cache: TtlCache[int] = TtlCache(ttl_seconds=60, max_entries=2, clock=clock)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1
    cache.set("c", 3)  # evicts the oldest insert ("a")
    assert cache.get("a") is None and cache.get("b") == 2
    clock.now += 60
    assert cache.get("b") is None


def test_sliding_window_limiter():
    clock = _Clock()
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60, clock=clock)
    assert limiter.hit("u1") and limiter.hit("u1")
    assert not limiter.hit("u1")
    assert limiter.hit("u2")  # per key
    clock.now += 60
    assert limiter.hit("u1")
