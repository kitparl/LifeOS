from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.text import clean_text

NewsDatePreset = Literal["today", "yesterday", "24h", "48h", "7d", "30d"]
NewsSort = Literal["date", "relevance"]
SavedFilter = Literal["all", "recent", "expiring"]

URL_MAX = 2048
HOST_MAX = 253
# Allowlists for vendor filter values (validated at the API boundary).
COUNTRY_PATTERN = r"^[A-Z]{2}$"
LANG_PATTERN = r"^[a-z]{2,3}$"
HOST_PATTERN = r"^([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"


def is_http_url(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith("https://") or lowered.startswith("http://")


# --------------------------------------------------------------------------
# Live news (FreeNewsAPI proxy). Never persisted.
# --------------------------------------------------------------------------

class NewsArticle(BaseModel):
    """One vendor article. Everything except id/url/title may be missing upstream."""

    id: str
    url: str
    title: str
    description: str | None = None
    published_at: datetime | None = None
    host: str | None = None
    sitename: str | None = None
    country: str | None = None
    lang: str | None = None
    author: str | None = None
    categories: list[str] | None = None
    image: str | None = None
    # Current user's saved row for this URL (annotated per request, never cached).
    saved_article_id: str | None = None


class NewsArticlePage(BaseModel):
    items: list[NewsArticle]
    total: int
    total_is_lower_bound: bool = False
    offset: int
    limit: int
    has_more: bool


class NewsArticleDetail(NewsArticle):
    # First paragraphs of the body only; the full body is never returned or stored.
    excerpt: list[str] = Field(default_factory=list)


class NewsCategory(BaseModel):
    id: str
    label: str


# --------------------------------------------------------------------------
# Saved articles (user library)
# --------------------------------------------------------------------------

class SavedArticleCreate(BaseModel):
    article_external_id: str | None = Field(default=None, max_length=64)
    article_url: str = Field(min_length=1, max_length=URL_MAX)
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    image: str | None = Field(default=None, max_length=URL_MAX)
    publisher: str | None = Field(default=None, max_length=200)
    host: str | None = Field(default=None, max_length=HOST_MAX)
    author: str | None = Field(default=None, max_length=200)
    published_at: datetime | None = None

    @field_validator("article_url")
    @classmethod
    def _article_url_is_http(cls, v: str) -> str:
        v = v.strip()
        if not is_http_url(v):
            raise ValueError("article_url must be an http(s) URL")
        return v

    @field_validator("image")
    @classmethod
    def _image_is_http(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v if v and is_http_url(v) else None

    @field_validator("title", "description", "publisher", "host", "author", "article_external_id")
    @classmethod
    def _plain_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return clean_text(v) or None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, v: str | None) -> str:
        if not v:
            raise ValueError("title must not be blank")
        return v


class SavedArticleResponse(BaseModel):
    id: str
    article_external_id: str | None
    article_url: str
    title: str
    description: str | None
    image: str | None
    publisher: str | None
    host: str | None
    author: str | None
    published_at: datetime | None
    saved_at: datetime
    expires_at: datetime
    collection_ids: list[str] = Field(default_factory=list)
    already_saved: bool = False


class SavedArticlePage(BaseModel):
    items: list[SavedArticleResponse]
    total: int


# --------------------------------------------------------------------------
# Collections
# --------------------------------------------------------------------------

class _CollectionName(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def _clean_name(cls, v: str) -> str:
        v = clean_text(v)
        if not v:
            raise ValueError("name must not be blank")
        return v


class CollectionCreate(_CollectionName):
    pass


class CollectionUpdate(_CollectionName):
    pass


class CollectionResponse(BaseModel):
    id: str
    name: str
    article_count: int
    created_at: datetime
    updated_at: datetime


class MembershipAdd(BaseModel):
    saved_article_id: str = Field(min_length=1, max_length=36)


class MembershipMove(BaseModel):
    target_collection_id: str = Field(min_length=1, max_length=36)
