"""News: FreeNewsAPI proxy (live, never persisted) + the user's saved-article library and collections."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import TtlCache
from app.core.config import Settings, get_settings
from app.core.exceptions import (
    AppError,
    BadGatewayError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    TooManyRequestsError,
    get_or_404,
)
from app.core.pagination import Pagination
from app.core.rate_limit import SlidingWindowLimiter
from app.core.text import clean_text
from app.core.timezone import as_utc, utc_now
from app.modules.news import categories
from app.modules.news.client import (
    FreeNewsClient,
    NewsApiError,
    NewsApiMalformedResponseError,
    NewsApiRateLimitError,
    NewsSearchResult,
)
from app.modules.news.dedupe import dedupe_articles
from app.modules.news.models import NewsCollection, NewsSavedArticle
from app.modules.news.repository import NewsRepository
from app.modules.news.schemas import (
    CollectionResponse,
    NewsArticle,
    NewsArticleDetail,
    NewsArticlePage,
    NewsCategory,
    NewsDatePreset,
    NewsSort,
    SavedArticleCreate,
    SavedArticlePage,
    SavedArticleResponse,
    SavedFilter,
)

logger = logging.getLogger(__name__)

VENDOR_CACHE_TTL_SECONDS = 60
VENDOR_CACHE_MAX_ENTRIES = 256
VENDOR_MAX_OFFSET = 9900
EXCERPT_MAX_PARAGRAPHS = 3
EXCERPT_MAX_CHARS = 1200
_PARAGRAPH_SPLIT_RE = re.compile(r"\n+")
# NewsAPI-style truncation marker some bodies end with, e.g. "… [+2384 chars]".
_TRUNCATION_MARKER_RE = re.compile(r"\s*…?\s*\[\+\d+ chars\]\s*$")

# Process-local vendor state: short-lived response cache and per-user proxy limiter.
_vendor_cache: TtlCache[NewsSearchResult | NewsArticleDetail] = TtlCache(
    VENDOR_CACHE_TTL_SECONDS, VENDOR_CACHE_MAX_ENTRIES
)
_proxy_limiter: SlidingWindowLimiter | None = None


def reset_vendor_state() -> None:
    """Clear the response cache and proxy limiter (tests; settings changes)."""
    global _proxy_limiter
    _vendor_cache.clear()
    _proxy_limiter = None


def _limiter(settings: Settings) -> SlidingWindowLimiter:
    global _proxy_limiter
    if _proxy_limiter is None:
        _proxy_limiter = SlidingWindowLimiter(settings.news_proxy_per_minute, 60)
    return _proxy_limiter



def _to_app_error(exc: NewsApiError) -> AppError:
    """Map a vendor error to the {"code", "message"} detail shape used for vendor errors."""
    detail = {"code": exc.code, "message": str(exc)}
    if isinstance(exc, NewsApiRateLimitError):
        return TooManyRequestsError(detail)
    if isinstance(exc, NewsApiMalformedResponseError):
        return BadGatewayError(detail)
    return ServiceUnavailableError(detail)


def build_excerpt(text: str | None) -> list[str]:
    """First paragraphs of an article body, capped; the full body is never returned."""
    if not text:
        return []
    paragraphs = [clean_text(p) for p in _PARAGRAPH_SPLIT_RE.split(text)]
    excerpt: list[str] = []
    budget = EXCERPT_MAX_CHARS
    for paragraph in (p for p in paragraphs if p):
        paragraph = _TRUNCATION_MARKER_RE.sub("", paragraph)
        if not paragraph:
            continue
        if len(paragraph) > budget:
            cut = paragraph[:budget].rsplit(" ", 1)[0].rstrip(" ,;:.")
            if cut:
                excerpt.append(f"{cut}…")
            break
        excerpt.append(paragraph)
        budget -= len(paragraph)
        if len(excerpt) == EXCERPT_MAX_PARAGRAPHS or budget <= 0:
            break
    return excerpt


@dataclass(frozen=True)
class ArticleQuery:
    q: str | None = None
    category: str | None = None
    country: str | None = None
    lang: str | None = None
    host: str | None = None
    date: NewsDatePreset | None = None
    sort: NewsSort = "date"
    limit: int = 20
    offset: int = 0


def _vendor_params(query: ArticleQuery) -> dict[str, str | int]:
    """Documented `/v1/search` params. Category mappings win over overlapping filters."""
    params: dict[str, str | int] = {"sort": query.sort, "size": query.limit, "offset": query.offset}
    filters = {"q": query.q, "country": query.country, "lang": query.lang, "host": query.host, "date": query.date}
    params.update({k: v for k, v in filters.items() if v})
    if query.category:
        params.update(categories.resolve(query.category))
    return params


def _cache_key(path: str, params: dict[str, str | int]) -> str:
    return path + "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))


class NewsService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.repo = NewsRepository(db)
        self.settings = settings or get_settings()

    # ------------------------------------------------------------------ live news

    @staticmethod
    def list_categories() -> list[NewsCategory]:
        return [NewsCategory(id=c.id, label=c.label) for c in categories.CATEGORIES]

    def _enforce_proxy_limit(self, key: str) -> None:
        if not _limiter(self.settings).hit(key):
            raise TooManyRequestsError(
                {"code": "rate_limit", "message": "Too many news requests. Please wait a moment."}
            )

    async def articles(self, user_id: str | None, query: ArticleQuery, *, proxy_key: str) -> NewsArticlePage:
        """Live search. `user_id` is None for anonymous (Explore) callers: no saved-state lookup."""
        if query.q and query.category:
            raise BadRequestError("Use either a search query or a category, not both")
        self._enforce_proxy_limit(proxy_key)
        params = _vendor_params(query)
        key = _cache_key("/v1/search", params)
        result = _vendor_cache.get(key)
        if not isinstance(result, NewsSearchResult):
            try:
                result = await FreeNewsClient(self.settings.freenews_api_base_url).search(params)
            except NewsApiError as exc:
                logger.warning("FreeNewsAPI search failed: %s", exc.code)
                raise _to_app_error(exc) from exc
            _vendor_cache.set(key, result)

        items = await self._annotate_saved(user_id, dedupe_articles(result.articles))
        next_offset = query.offset + query.limit
        return NewsArticlePage(
            items=items,
            total=result.total,
            total_is_lower_bound=result.total_is_lower_bound,
            offset=query.offset,
            limit=query.limit,
            has_more=bool(result.articles) and next_offset < result.total and next_offset <= VENDOR_MAX_OFFSET,
        )

    async def article_detail(self, user_id: str | None, url: str, *, proxy_key: str) -> NewsArticleDetail:
        self._enforce_proxy_limit(proxy_key)
        key = _cache_key("/v1/article", {"url": url})
        detail = _vendor_cache.get(key)
        if not isinstance(detail, NewsArticleDetail):
            try:
                found = await FreeNewsClient(self.settings.freenews_api_base_url).article(url)
            except NewsApiError as exc:
                logger.warning("FreeNewsAPI article failed: %s", exc.code)
                raise _to_app_error(exc) from exc
            if found is None:
                raise NotFoundError({"code": "article_unavailable", "message": "This article is no longer available."})
            detail = NewsArticleDetail(**found.article.model_dump(), excerpt=build_excerpt(found.text))
            _vendor_cache.set(key, detail)

        if user_id is None:
            return detail
        saved = await self.repo.saved_ids_for_urls(user_id, [detail.url], utc_now())
        return detail.model_copy(update={"saved_article_id": saved.get(detail.url)})

    async def _annotate_saved(self, user_id: str | None, articles: list[NewsArticle]) -> list[NewsArticle]:
        if user_id is None:
            return articles
        saved = await self.repo.saved_ids_for_urls(user_id, [a.url for a in articles], utc_now())
        return [a.model_copy(update={"saved_article_id": saved.get(a.url)}) for a in articles]

    # ------------------------------------------------------------------ saved articles

    async def _enforce_write_limit(self, user_id: str, now: datetime) -> None:
        if await self.repo.writes_since(user_id, now - timedelta(hours=1)) >= self.settings.news_writes_per_hour:
            raise TooManyRequestsError(
                {"code": "write_limit", "message": "Too many saves this hour. Please try again later."}
            )

    async def _saved_response(self, saved: NewsSavedArticle, *, already_saved: bool = False) -> SavedArticleResponse:
        collection_ids = (await self.repo.collection_ids_for([saved.id])).get(saved.id, [])
        return self._to_saved_response(saved, collection_ids, already_saved=already_saved)

    @staticmethod
    def _to_saved_response(
        saved: NewsSavedArticle, collection_ids: list[str], *, already_saved: bool = False
    ) -> SavedArticleResponse:
        return SavedArticleResponse(
            id=saved.id,
            article_external_id=saved.article_external_id,
            article_url=saved.article_url,
            title=saved.title,
            description=saved.description,
            image=saved.image,
            publisher=saved.publisher,
            host=saved.host,
            author=saved.author,
            published_at=as_utc(saved.published_at) if saved.published_at else None,
            saved_at=as_utc(saved.saved_at),
            expires_at=as_utc(saved.expires_at),
            collection_ids=collection_ids,
            already_saved=already_saved,
        )

    async def save(self, user_id: str, data: SavedArticleCreate) -> tuple[SavedArticleResponse, bool]:
        """Save a metadata snapshot. Returns (article, created); an existing live save is returned as is."""
        now = utc_now()
        existing = await self.repo.get_saved_by_url(user_id, data.article_url)
        if existing is not None:
            if as_utc(existing.expires_at) > now:
                return await self._saved_response(existing, already_saved=True), False
            await self.repo.delete_saved(existing)

        await self._enforce_write_limit(user_id, now)
        saved = NewsSavedArticle(
            user_id=user_id,
            **data.model_dump(),
            saved_at=now,
            expires_at=now + timedelta(days=self.settings.article_retention_days),
        )
        try:
            async with self.repo.db.begin_nested():
                saved = await self.repo.create_saved(saved)
        except IntegrityError:
            # A concurrent request saved the same URL first.
            existing = await self.repo.get_saved_by_url(user_id, data.article_url)
            if existing is None:
                raise
            return await self._saved_response(existing, already_saved=True), False
        return self._to_saved_response(saved, []), True

    async def list_saved(self, user_id: str, saved_filter: SavedFilter, pagination: Pagination) -> SavedArticlePage:
        now = utc_now()
        await self.repo.purge_expired(now, user_id)
        rows, total = await self.repo.list_saved(user_id, saved_filter, now, pagination)
        return await self._saved_page(rows, total)

    async def _saved_page(self, rows: list[NewsSavedArticle], total: int) -> SavedArticlePage:
        collection_ids = await self.repo.collection_ids_for([r.id for r in rows])
        return SavedArticlePage(
            items=[self._to_saved_response(r, collection_ids.get(r.id, [])) for r in rows], total=total
        )

    async def _get_live_saved(self, user_id: str, saved_id: str) -> NewsSavedArticle:
        saved = get_or_404(await self.repo.get_saved(user_id, saved_id), "Saved article not found")
        if as_utc(saved.expires_at) <= utc_now():
            raise NotFoundError("Saved article not found")
        return saved

    async def delete_saved(self, user_id: str, saved_id: str) -> None:
        saved = get_or_404(await self.repo.get_saved(user_id, saved_id), "Saved article not found")
        await self.repo.delete_saved(saved)

    async def purge_expired(self) -> int:
        """Scheduled cleanup for every user."""
        return await self.repo.purge_expired(utc_now())

    # ------------------------------------------------------------------ collections

    @staticmethod
    def _to_collection_response(collection: NewsCollection, count: int) -> CollectionResponse:
        return CollectionResponse(
            id=collection.id,
            name=collection.name,
            article_count=count,
            created_at=as_utc(collection.created_at),
            updated_at=as_utc(collection.updated_at),
        )

    async def _get_collection(self, user_id: str, collection_id: str) -> NewsCollection:
        return get_or_404(await self.repo.get_collection(user_id, collection_id), "Collection not found")

    async def _ensure_unique_name(self, user_id: str, name: str, exclude_id: str | None = None) -> None:
        clash = await self.repo.find_collection_by_name(user_id, name)
        if clash is not None and clash.id != exclude_id:
            raise ConflictError("A collection with this name already exists")

    async def list_collections(self, user_id: str) -> list[CollectionResponse]:
        now = utc_now()
        await self.repo.purge_expired(now, user_id)
        rows = await self.repo.list_collections_with_counts(user_id, now)
        return [self._to_collection_response(c, n) for c, n in rows]

    async def create_collection(self, user_id: str, name: str) -> CollectionResponse:
        await self._ensure_unique_name(user_id, name)
        await self._enforce_write_limit(user_id, utc_now())
        collection = await self.repo.create_collection(user_id, name)
        return self._to_collection_response(collection, 0)

    async def rename_collection(self, user_id: str, collection_id: str, name: str) -> CollectionResponse:
        collection = await self._get_collection(user_id, collection_id)
        await self._ensure_unique_name(user_id, name, exclude_id=collection.id)
        collection = await self.repo.rename_collection(collection, name)
        count = await self.repo.count_members(collection.id, utc_now())
        return self._to_collection_response(collection, count)

    async def delete_collection(self, user_id: str, collection_id: str) -> None:
        """Removes the collection and its memberships; the saved articles themselves stay."""
        collection = await self._get_collection(user_id, collection_id)
        await self.repo.delete_collection(collection)

    async def list_collection_articles(
        self, user_id: str, collection_id: str, pagination: Pagination
    ) -> SavedArticlePage:
        collection = await self._get_collection(user_id, collection_id)
        now = utc_now()
        await self.repo.purge_expired(now, user_id)
        rows, total = await self.repo.list_members(collection.id, now, pagination)
        return await self._saved_page(rows, total)

    async def add_to_collection(self, user_id: str, collection_id: str, saved_id: str) -> SavedArticleResponse:
        """Idempotent: adding an existing member is a no-op."""
        collection = await self._get_collection(user_id, collection_id)
        saved = await self._get_live_saved(user_id, saved_id)
        if await self.repo.get_membership(collection.id, saved.id) is None:
            await self.repo.add_membership(collection.id, saved.id)
        return await self._saved_response(saved)

    async def remove_from_collection(self, user_id: str, collection_id: str, saved_id: str) -> None:
        collection = await self._get_collection(user_id, collection_id)
        saved = get_or_404(await self.repo.get_saved(user_id, saved_id), "Saved article not found")
        membership = get_or_404(await self.repo.get_membership(collection.id, saved.id), "Article is not in this collection")
        await self.repo.remove_membership(membership)

    async def move_between_collections(
        self, user_id: str, collection_id: str, saved_id: str, target_collection_id: str
    ) -> SavedArticleResponse:
        """Move a member to another collection in one transaction (the request's session)."""
        source = await self._get_collection(user_id, collection_id)
        target = await self._get_collection(user_id, target_collection_id)
        if source.id == target.id:
            raise BadRequestError("Choose a different collection to move to")
        saved = await self._get_live_saved(user_id, saved_id)
        membership = get_or_404(await self.repo.get_membership(source.id, saved.id), "Article is not in this collection")
        if await self.repo.get_membership(target.id, saved.id) is None:
            await self.repo.add_membership(target.id, saved.id)
        await self.repo.remove_membership(membership)
        return await self._saved_response(saved)
