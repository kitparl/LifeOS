"""Thin FreeNewsAPI client (https://freenewsapi.ai, free API key required). The only code that knows vendor URLs.

The key is sent as a bearer token, never in the URL, so it cannot leak through request logging.

The client takes several keys and fails over: a key that is rejected (401/403), rate limited (429) or
out of monthly quota (402) is parked (see `key_pool`) and the next key is tried. Other failures
(5xx, timeouts) say nothing about the key, so they do not rotate.

Only documented `/v1/search` and `/v1/article` parameters are sent. Responses are parsed
defensively: every field except id/url/title may be missing, and text arrives with HTML
entities. Error `code` values match the AI adapters' and Wordnik's so the frontend handles
vendor failures uniformly.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.text import clean_text
from app.core.timezone import utc_now
from app.modules.news import key_pool
from app.modules.news.key_pool import KeyState
from app.modules.news.schemas import NewsArticle, is_http_url

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10.0
_LABEL = "FreeNewsAPI"
DEFAULT_RATE_LIMIT_COOLDOWN_SECONDS = 60
MAX_RATE_LIMIT_COOLDOWN_SECONDS = 300
INVALID_KEY_COOLDOWN = timedelta(hours=1)


class NewsApiError(Exception):
    """Base error for every FreeNewsAPI call. `code` is a stable, client-facing identifier."""

    code: str = "provider_unavailable"


class NewsApiMissingCredentialError(NewsApiError):
    code = "missing_credential"


class NewsApiKeyError(NewsApiError):
    """The key itself cannot serve requests right now. Another key may; `retry_at` is when this one may."""

    state: KeyState
    retry_at: datetime | None

    def __init__(self, message: str, retry_at: datetime | None = None):
        super().__init__(message)
        self.retry_at = retry_at


class NewsApiInvalidCredentialError(NewsApiKeyError):
    code = "invalid_credential"
    state = "invalid"


class NewsApiRateLimitError(NewsApiKeyError):
    code = "rate_limit"
    state = "rate_limited"


class NewsApiQuotaExhaustedError(NewsApiKeyError):
    code = "quota_exhausted"
    state = "quota_exhausted"


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


_KEY_ERRORS: dict[KeyState, tuple[type[NewsApiKeyError], str]] = {
    "invalid": (NewsApiInvalidCredentialError, f"Invalid or revoked {_LABEL} API key. Check Integrations."),
    "rate_limited": (NewsApiRateLimitError, f"{_LABEL} rate limit reached. Try again shortly."),
    "quota_exhausted": (
        NewsApiQuotaExhaustedError,
        f"{_LABEL} monthly quota is used up. Add another key in Integrations or wait for it to renew.",
    ),
}


def _key_error(state: KeyState, retry_at: datetime | None = None) -> NewsApiKeyError:
    error_type, message = _KEY_ERRORS[state]
    return error_type(message, retry_at)


def _next_month_start(now: datetime) -> datetime:
    year, month = (now.year + 1, 1) if now.month == 12 else (now.year, now.month + 1)
    return datetime(year, month, 1, tzinfo=timezone.utc)


def _rate_limit_retry_at(res: httpx.Response) -> datetime:
    """`Retry-After` seconds (clamped); a missing or malformed header means the default cooldown."""
    try:
        seconds = int(res.headers.get("Retry-After", ""))
    except ValueError:
        seconds = DEFAULT_RATE_LIMIT_COOLDOWN_SECONDS
    return utc_now() + timedelta(seconds=min(max(seconds, 1), MAX_RATE_LIMIT_COOLDOWN_SECONDS))


def _quota_retry_at(res: httpx.Response) -> datetime:
    """The 402 body's `renews_at`, else the first of next month (UTC), when the monthly allowance renews."""
    now = utc_now()
    try:
        renews_at = _parse_datetime(res.json().get("renews_at"))
    except (ValueError, AttributeError):
        renews_at = None
    if renews_at is not None:
        return renews_at if renews_at.tzinfo else renews_at.replace(tzinfo=timezone.utc)
    return _next_month_start(now)


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
    def __init__(self, api_keys: Sequence[str], base_url: str | None = None):
        self._api_keys = [k for k in api_keys if k]
        if not self._api_keys:
            raise NewsApiMissingCredentialError("Add a FreeNewsAPI key in Integrations first.")
        self._base_url = (base_url or get_settings().freenews_api_base_url).rstrip("/")

    async def _get(self, path: str, params: dict[str, Any]) -> Any:
        """GET a vendor path, failing over across keys. Returns decoded JSON, or None when the vendor has no entry (404)."""
        last_error: NewsApiKeyError | None = None
        for key in self._api_keys:
            parked = key_pool.parked(key)
            if parked is not None:
                last_error = last_error or _key_error(parked.state, parked.until)
                continue
            try:
                return await self._get_with_key(key, path, params)
            except NewsApiKeyError as exc:
                key_pool.park(key, exc.state, exc.retry_at or utc_now() + INVALID_KEY_COOLDOWN)
                logger.warning(
                    "FreeNewsAPI key %s unusable (%s); trying the next key", key_pool.fingerprint(key), exc.code
                )
                last_error = exc
        assert last_error is not None  # `_api_keys` is non-empty and every key either failed or is parked
        raise last_error

    async def _get_with_key(self, key: str, path: str, params: dict[str, Any]) -> Any:
        try:
            async with _http_client(TIMEOUT_SECONDS) as client:
                res = await client.get(
                    f"{self._base_url}{path}", params=params, headers={"Authorization": f"Bearer {key}"}
                )
        except httpx.TimeoutException as exc:
            raise NewsApiTimeoutError(f"{_LABEL} request timed out.") from exc
        except httpx.HTTPError as exc:
            raise NewsApiUnavailableError(f"{_LABEL} is temporarily unavailable.") from exc

        if res.status_code in (httpx.codes.UNAUTHORIZED, httpx.codes.FORBIDDEN):
            raise _key_error("invalid", utc_now() + INVALID_KEY_COOLDOWN)
        if res.status_code == httpx.codes.PAYMENT_REQUIRED:
            raise _key_error("quota_exhausted", _quota_retry_at(res))
        if res.status_code == httpx.codes.TOO_MANY_REQUESTS:
            raise _key_error("rate_limited", _rate_limit_retry_at(res))
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
