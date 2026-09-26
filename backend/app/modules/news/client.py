"""Thin FreeNewsAPI client (https://freenewsapi.ai, no API key). The only code that knows vendor URLs.

Only documented `/v1/search` and `/v1/article` parameters are sent. Responses are parsed
defensively: every field except id/url/title may be missing, and text arrives with HTML
entities. Error `code` values match the AI adapters' and Wordnik's so the frontend handles
vendor failures uniformly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.text import clean_text
from app.modules.news.schemas import NewsArticle, is_http_url

TIMEOUT_SECONDS = 10.0
_LABEL = "FreeNewsAPI"


class NewsApiError(Exception):
    """Base error for every FreeNewsAPI call. `code` is a stable, client-facing identifier."""

    code: str = "provider_unavailable"


class NewsApiRateLimitError(NewsApiError):
    code = "rate_limit"


class NewsApiTimeoutError(NewsApiError):
    code = "timeout"


class NewsApiUnavailableError(NewsApiError):
    code = "provider_unavailable"


class NewsApiMalformedResponseError(NewsApiError):
    code = "malformed_response"


@dataclass(frozen=True)
class NewsSearchResult:
    articles: list[NewsArticle]
    total: int
    total_is_lower_bound: bool


@dataclass(frozen=True)
class NewsArticleWithBody:
    article: NewsArticle
    text: str | None


def _http_client(timeout: float) -> httpx.AsyncClient:
    """Single construction point for FreeNewsAPI HTTP clients (tests patch this seam)."""
    return httpx.AsyncClient(timeout=timeout)


def _optional_text(value: Any) -> str | None:
    return clean_text(value) or None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_categories(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    cats = [c for c in (clean_text(v) for v in value if isinstance(v, str)) if c]
    return cats or None


def parse_article(raw: Any) -> NewsArticle | None:
    """A NewsArticle from one vendor result, or None when it lacks a usable url/title."""
    if not isinstance(raw, dict):
        return None
    url = raw.get("url")
    title = clean_text(raw.get("title"))
    if not isinstance(url, str) or not is_http_url(url.strip()) or not title:
        return None
    url = url.strip()
    image = raw.get("image")
    raw_id = raw.get("id")
    return NewsArticle(
        id=str(raw_id) if isinstance(raw_id, (str, int)) and str(raw_id) else url,
        url=url,
        title=title,
        description=_optional_text(raw.get("description")),
        published_at=_parse_datetime(raw.get("published_at")),
        host=_optional_text(raw.get("host")),
        sitename=_optional_text(raw.get("sitename")),
        country=_optional_text(raw.get("country")),
        lang=_optional_text(raw.get("lang")),
        author=_optional_text(raw.get("author")),
        categories=_parse_categories(raw.get("categories")),
        image=image.strip() if isinstance(image, str) and is_http_url(image.strip()) else None,
    )


class FreeNewsClient:
    def __init__(self, base_url: str | None = None):
        self._base_url = (base_url or get_settings().freenews_api_base_url).rstrip("/")

    async def _get(self, path: str, params: dict[str, Any]) -> Any:
        """GET a vendor path. Returns decoded JSON, or None when the vendor has no entry (404)."""
        try:
            async with _http_client(TIMEOUT_SECONDS) as client:
                res = await client.get(f"{self._base_url}{path}", params=params)
        except httpx.TimeoutException as exc:
            raise NewsApiTimeoutError(f"{_LABEL} request timed out.") from exc
        except httpx.HTTPError as exc:
            raise NewsApiUnavailableError(f"{_LABEL} is temporarily unavailable.") from exc

        if res.status_code == httpx.codes.TOO_MANY_REQUESTS:
            raise NewsApiRateLimitError(f"{_LABEL} rate limit reached. Try again shortly.")
        if res.status_code == httpx.codes.NOT_FOUND:
            return None
        if res.status_code >= httpx.codes.BAD_REQUEST:
            raise NewsApiUnavailableError(f"{_LABEL} could not complete the request (HTTP {res.status_code}).")
        try:
            return res.json()
        except ValueError as exc:
            raise NewsApiMalformedResponseError(f"{_LABEL} returned a non-JSON response.") from exc

    async def search(self, params: dict[str, str | int]) -> NewsSearchResult:
        """`/v1/search`. `params` must hold documented parameters only (built by the service)."""
        data = await self._get("/v1/search", params)
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise NewsApiMalformedResponseError(f"{_LABEL} returned an unexpected search response.")
        articles = [a for a in (parse_article(r) for r in data["results"]) if a is not None]
        total = data.get("total")
        return NewsSearchResult(
            articles=articles,
            total=total if isinstance(total, int) and total >= 0 else len(articles),
            total_is_lower_bound=data.get("total_is_lower_bound") is True,
        )

    async def article(self, url: str) -> NewsArticleWithBody | None:
        """`/v1/article` for one exact URL, with its body text. None when the vendor has no such article."""
        data = await self._get("/v1/article", {"url": url, "full_text": "true"})
        if data is None:
            return None
        article = parse_article(data)
        if article is None:
            raise NewsApiMalformedResponseError(f"{_LABEL} returned an unexpected article response.")
        text = data.get("text")
        return NewsArticleWithBody(article=article, text=text if isinstance(text, str) else None)
