from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, new_id
from app.core.timezone import utc_now


class ContentEmbedding(Base):
    __tablename__ = "content_embeddings"
    __table_args__ = (UniqueConstraint("user_id", "source_type", "source_id", name="uq_embedding_source"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    route: Mapped[str] = mapped_column(String(200), nullable=False)
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class AIUseCaseModelSelection(Base):
    """Current provider/model pointer for a user + use case."""

    __tablename__ = "ai_use_case_model_selections"
    __table_args__ = (UniqueConstraint("user_id", "use_case", name="uq_ai_use_case_selection"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    use_case: Mapped[str] = mapped_column(String(80), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class AIUseCaseModelSelectionHistory(Base):
    """Append-only history of model selections with active date ranges."""

    __tablename__ = "ai_use_case_model_selection_history"
    __table_args__ = (
        Index("ix_ai_use_case_history_lookup", "user_id", "use_case", "effective_from"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    use_case: Mapped[str] = mapped_column(String(80), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


MODEL_SOURCE_FETCHED = "fetched"
MODEL_SOURCE_MANUAL = "manual"


class AIProviderModel(Base):
    """Cached model catalog per user + provider, replaced on each refresh."""

    __tablename__ = "ai_provider_models"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", "model_id", name="uq_ai_provider_model"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model_id: Mapped[str] = mapped_column(String(80), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Comma-separated capability flags, e.g. "chat,vision".
    capabilities: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    # "fetched" rows are replaced on each refresh; "manual" rows (user-added ids) persist.
    source: Mapped[str] = mapped_column(String(16), nullable=False, default=MODEL_SOURCE_FETCHED)
    refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    @property
    def capability_set(self) -> frozenset[str]:
        return frozenset(c for c in self.capabilities.split(",") if c)
