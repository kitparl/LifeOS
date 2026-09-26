from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from pydantic import AfterValidator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.core.pagination import Pagination, pagination_params
from app.modules.auth.models import User
from app.modules.news.categories import CATEGORY_IDS
from app.modules.news.schemas import (
    COUNTRY_PATTERN,
    HOST_PATTERN,
    LANG_PATTERN,
    URL_MAX,
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
    MembershipAdd,
    MembershipMove,
    NewsArticleDetail,
    NewsArticlePage,
    NewsCategory,
    NewsDatePreset,
    NewsSort,
    SavedArticleCreate,
    SavedArticlePage,
    SavedArticleResponse,
    SavedFilter,
    is_http_url,
)
from app.modules.news.rate_limit import proxy_limit_key
from app.modules.news.service import VENDOR_MAX_OFFSET, ArticleQuery, NewsService

router = APIRouter(prefix="/news", tags=["news"])


def _known_category(value: str | None) -> str | None:
    if value is not None and value not in CATEGORY_IDS:
        raise ValueError("Unknown category")
    return value


def _http_url(value: str) -> str:
    value = value.strip()
    if not is_http_url(value):
        raise ValueError("url must be an http(s) URL")
    return value


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


SearchParam = Annotated[str | None, AfterValidator(_blank_to_none), Query(max_length=200)]
CategoryParam = Annotated[str | None, AfterValidator(_known_category), Query(max_length=32)]
ArticleUrlParam = Annotated[str, AfterValidator(_http_url), Query(max_length=URL_MAX)]


def _proxy_key(user: User | None, request: Request) -> str:
    return proxy_limit_key(user.id if user else None, request.client.host if request.client else None)


# ------------------------------------------------------------------ live news (public: Explore guests browse too)
# Signed-in callers get saved-state annotations; anonymous callers get `saved_article_id: null`.


@router.get("/categories", response_model=list[NewsCategory])
async def list_news_categories():
    return NewsService.list_categories()


@router.get("/articles", response_model=NewsArticlePage)
async def list_news_articles(
    request: Request,
    q: SearchParam = None,
    category: CategoryParam = None,
    country: str | None = Query(default=None, pattern=COUNTRY_PATTERN),
    lang: str | None = Query(default=None, pattern=LANG_PATTERN),
    host: str | None = Query(default=None, max_length=253, pattern=HOST_PATTERN),
    date: NewsDatePreset | None = Query(default=None),
    sort: NewsSort = Query(default="date"),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0, le=VENDOR_MAX_OFFSET),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    query = ArticleQuery(
        q=q, category=category, country=country, lang=lang, host=host, date=date, sort=sort, limit=limit, offset=offset
    )
    return await NewsService(db).articles(user.id if user else None, query, proxy_key=_proxy_key(user, request))


@router.get("/article", response_model=NewsArticleDetail)
async def get_news_article(
    request: Request,
    url: ArticleUrlParam,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    return await NewsService(db).article_detail(user.id if user else None, url, proxy_key=_proxy_key(user, request))


# ------------------------------------------------------------------ saved articles (account only)

@router.get("/saved", response_model=SavedArticlePage)
async def list_saved_articles(
    filter: SavedFilter = Query(default="all"),
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NewsService(db).list_saved(user.id, filter, pagination)


@router.post("/saved", response_model=SavedArticleResponse, status_code=status.HTTP_201_CREATED)
async def save_article(
    data: SavedArticleCreate,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    saved, created = await NewsService(db).save(user.id, data)
    if not created:
        response.status_code = status.HTTP_200_OK
    return saved


@router.delete("/saved/{saved_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_article(
    saved_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await NewsService(db).delete_saved(user.id, saved_id)


# ------------------------------------------------------------------ collections (account only)

@router.get("/collections", response_model=list[CollectionResponse])
async def list_collections(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NewsService(db).list_collections(user.id)


@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    data: CollectionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NewsService(db).create_collection(user.id, data.name)


@router.patch("/collections/{collection_id}", response_model=CollectionResponse)
async def rename_collection(
    collection_id: str,
    data: CollectionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NewsService(db).rename_collection(user.id, collection_id, data.name)


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await NewsService(db).delete_collection(user.id, collection_id)


@router.get("/collections/{collection_id}/articles", response_model=SavedArticlePage)
async def list_collection_articles(
    collection_id: str,
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NewsService(db).list_collection_articles(user.id, collection_id, pagination)


@router.post("/collections/{collection_id}/articles", response_model=SavedArticleResponse)
async def add_article_to_collection(
    collection_id: str,
    data: MembershipAdd,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NewsService(db).add_to_collection(user.id, collection_id, data.saved_article_id)


@router.delete("/collections/{collection_id}/articles/{saved_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_article_from_collection(
    collection_id: str,
    saved_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await NewsService(db).remove_from_collection(user.id, collection_id, saved_id)


@router.post("/collections/{collection_id}/articles/{saved_id}/move", response_model=SavedArticleResponse)
async def move_article_between_collections(
    collection_id: str,
    saved_id: str,
    data: MembershipMove,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await NewsService(db).move_between_collections(user.id, collection_id, saved_id, data.target_collection_id)

