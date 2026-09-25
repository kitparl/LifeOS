"""Queries for the user news library. Every user-facing query is scoped by `user_id`.

Membership rows are deleted explicitly before their saved article or collection, so SQLite
(without `PRAGMA foreign_keys`) behaves like Postgres' ON DELETE CASCADE.
"""

from datetime import datetime, timedelta

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.modules.news.models import NewsCollection, NewsCollectionArticle, NewsSavedArticle
from app.modules.news.schemas import SavedFilter

RECENT_DAYS = 7
EXPIRING_SOON_DAYS = 3


class NewsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ expiry

    async def purge_expired(self, now: datetime, user_id: str | None = None) -> int:
        """Delete expired saved articles (one user's, or everyone's) and their memberships."""
        expired = select(NewsSavedArticle.id).where(NewsSavedArticle.expires_at <= now)
        if user_id is not None:
            expired = expired.where(NewsSavedArticle.user_id == user_id)
        await self.db.execute(
            delete(NewsCollectionArticle).where(NewsCollectionArticle.saved_article_id.in_(expired))
        )
        result = await self.db.execute(delete(NewsSavedArticle).where(NewsSavedArticle.id.in_(expired)))
        await self.db.flush()
        return result.rowcount or 0

    async def writes_since(self, user_id: str, since: datetime) -> int:
        saved = await self.db.execute(
            select(func.count())
            .select_from(NewsSavedArticle)
            .where(NewsSavedArticle.user_id == user_id, NewsSavedArticle.created_at >= since)
        )
        collections = await self.db.execute(
            select(func.count())
            .select_from(NewsCollection)
            .where(NewsCollection.user_id == user_id, NewsCollection.created_at >= since)
        )
        return int(saved.scalar_one()) + int(collections.scalar_one())

    # ------------------------------------------------------------------ saved articles

    async def saved_ids_for_urls(self, user_id: str, urls: list[str], now: datetime) -> dict[str, str]:
        """{article_url: saved_article_id} for the user's non-expired saves among `urls`."""
        if not urls:
            return {}
        result = await self.db.execute(
            select(NewsSavedArticle.article_url, NewsSavedArticle.id).where(
                NewsSavedArticle.user_id == user_id,
                NewsSavedArticle.article_url.in_(urls),
                NewsSavedArticle.expires_at > now,
            )
        )
        return {url: saved_id for url, saved_id in result.all()}

    async def get_saved(self, user_id: str, saved_id: str) -> NewsSavedArticle | None:
        result = await self.db.execute(
            select(NewsSavedArticle).where(NewsSavedArticle.id == saved_id, NewsSavedArticle.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_saved_by_url(self, user_id: str, url: str) -> NewsSavedArticle | None:
        result = await self.db.execute(
            select(NewsSavedArticle).where(NewsSavedArticle.user_id == user_id, NewsSavedArticle.article_url == url)
        )
        return result.scalar_one_or_none()

    async def create_saved(self, saved: NewsSavedArticle) -> NewsSavedArticle:
        self.db.add(saved)
        await self.db.flush()
        await self.db.refresh(saved)
        return saved

    async def delete_saved(self, saved: NewsSavedArticle) -> None:
        await self.db.execute(
            delete(NewsCollectionArticle).where(NewsCollectionArticle.saved_article_id == saved.id)
        )
        await self.db.delete(saved)
        await self.db.flush()

    async def list_saved(
        self, user_id: str, saved_filter: SavedFilter, now: datetime, pagination: Pagination
    ) -> tuple[list[NewsSavedArticle], int]:
        stmt: Select = select(NewsSavedArticle).where(
            NewsSavedArticle.user_id == user_id, NewsSavedArticle.expires_at > now
        )
        if saved_filter == "recent":
            stmt = stmt.where(NewsSavedArticle.saved_at >= now - timedelta(days=RECENT_DAYS))
        if saved_filter == "expiring":
            stmt = stmt.where(NewsSavedArticle.expires_at <= now + timedelta(days=EXPIRING_SOON_DAYS)).order_by(
                NewsSavedArticle.expires_at.asc(), NewsSavedArticle.id
            )
        else:
            stmt = stmt.order_by(NewsSavedArticle.saved_at.desc(), NewsSavedArticle.id)
        return await paginate(self.db, stmt, pagination)

    async def collection_ids_for(self, saved_ids: list[str]) -> dict[str, list[str]]:
        """{saved_article_id: [collection_id, ...]} for the given (already user-scoped) saved ids."""
        if not saved_ids:
            return {}
        result = await self.db.execute(
            select(NewsCollectionArticle.saved_article_id, NewsCollectionArticle.collection_id).where(
                NewsCollectionArticle.saved_article_id.in_(saved_ids)
            )
        )
        out: dict[str, list[str]] = {}
        for saved_id, collection_id in result.all():
            out.setdefault(saved_id, []).append(collection_id)
        return out

    # ------------------------------------------------------------------ collections

    async def list_collections_with_counts(
        self, user_id: str, now: datetime
    ) -> list[tuple[NewsCollection, int]]:
        live_members = (
            select(NewsCollectionArticle.collection_id, func.count().label("n"))
            .join(NewsSavedArticle, NewsSavedArticle.id == NewsCollectionArticle.saved_article_id)
            .where(NewsSavedArticle.expires_at > now)
            .group_by(NewsCollectionArticle.collection_id)
            .subquery()
        )
        result = await self.db.execute(
            select(NewsCollection, func.coalesce(live_members.c.n, 0))
            .outerjoin(live_members, live_members.c.collection_id == NewsCollection.id)
            .where(NewsCollection.user_id == user_id)
            .order_by(func.lower(NewsCollection.name), NewsCollection.id)
        )
        return [(collection, int(count)) for collection, count in result.all()]

    async def count_members(self, collection_id: str, now: datetime) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(NewsCollectionArticle)
            .join(NewsSavedArticle, NewsSavedArticle.id == NewsCollectionArticle.saved_article_id)
            .where(NewsCollectionArticle.collection_id == collection_id, NewsSavedArticle.expires_at > now)
        )
        return int(result.scalar_one())

    async def get_collection(self, user_id: str, collection_id: str) -> NewsCollection | None:
        result = await self.db.execute(
            select(NewsCollection).where(NewsCollection.id == collection_id, NewsCollection.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def find_collection_by_name(self, user_id: str, name: str) -> NewsCollection | None:
        """Case-insensitive name match within the user's collections."""
        result = await self.db.execute(
            select(NewsCollection).where(
                NewsCollection.user_id == user_id, func.lower(NewsCollection.name) == name.lower()
            )
        )
        return result.scalars().first()

    async def create_collection(self, user_id: str, name: str) -> NewsCollection:
        collection = NewsCollection(user_id=user_id, name=name)
        self.db.add(collection)
        await self.db.flush()
        await self.db.refresh(collection)
        return collection

    async def rename_collection(self, collection: NewsCollection, name: str) -> NewsCollection:
        collection.name = name
        await self.db.flush()
        await self.db.refresh(collection)
        return collection

    async def delete_collection(self, collection: NewsCollection) -> None:
        await self.db.execute(
            delete(NewsCollectionArticle).where(NewsCollectionArticle.collection_id == collection.id)
        )
        await self.db.delete(collection)
        await self.db.flush()

    async def list_members(
        self, collection_id: str, now: datetime, pagination: Pagination
    ) -> tuple[list[NewsSavedArticle], int]:
        stmt = (
            select(NewsSavedArticle)
            .join(NewsCollectionArticle, NewsCollectionArticle.saved_article_id == NewsSavedArticle.id)
            .where(NewsCollectionArticle.collection_id == collection_id, NewsSavedArticle.expires_at > now)
            .order_by(NewsCollectionArticle.created_at.desc(), NewsSavedArticle.id)
        )
        return await paginate(self.db, stmt, pagination)

    # ------------------------------------------------------------------ memberships

    async def get_membership(self, collection_id: str, saved_id: str) -> NewsCollectionArticle | None:
        result = await self.db.execute(
            select(NewsCollectionArticle).where(
                NewsCollectionArticle.collection_id == collection_id,
                NewsCollectionArticle.saved_article_id == saved_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_membership(self, collection_id: str, saved_id: str) -> None:
        self.db.add(NewsCollectionArticle(collection_id=collection_id, saved_article_id=saved_id))
        await self.db.flush()

    async def remove_membership(self, membership: NewsCollectionArticle) -> None:
        await self.db.delete(membership)
        await self.db.flush()
