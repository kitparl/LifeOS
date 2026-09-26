"""User news library. This is NOT a news database: live news is never stored here.

Only lightweight snapshots of articles a user saved (expiring after ARTICLE_RETENTION_DAYS) and
the user's collections referencing them.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, new_id
from app.core.timezone import utc_now


class NewsSavedArticle(Base):
    __tablename__ = "news_saved_articles"
    __table_args__ = (
        UniqueConstraint("user_id", "article_url", name="uq_news_saved_user_url"),
        Index("ix_news_saved_user_expires", "user_id", "expires_at"),
        Index("ix_news_saved_user_saved", "user_id", "saved_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    article_external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    article_url: Mapped[str] = mapped_column(String(2048), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(200), nullable=True)
    host: Mapped[str | None] = mapped_column(String(253), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class NewsCollection(Base):
    __tablename__ = "news_collections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Unique per user, case-insensitively (enforced in the service).
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class NewsCollectionArticle(Base):
    """Membership of a saved article in a collection. Deleting either side removes only this row."""

    __tablename__ = "news_collection_articles"
    __table_args__ = (UniqueConstraint("collection_id", "saved_article_id", name="uq_news_collection_article"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    collection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("news_collections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    saved_article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("news_saved_articles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
