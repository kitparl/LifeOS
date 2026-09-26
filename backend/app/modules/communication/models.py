import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

WRITING_CATEGORIES = (
    "LinkedIn",
    "Blog",
    "Essay",
    "Notes",
    "HR Answer",
    "Technical Answer",
)
SPEAKING_CATEGORIES = ("hr", "technical", "elevator", "mock_interview")


class WritingPractice(Base):
    __tablename__ = "writing_practices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="Notes")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class WritingCategory(Base):
    """User-defined, reusable writing category registry (extensible taxonomy)."""

    __tablename__ = "writing_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_writing_categories_user_name"),)


class SpeakingPractice(Base):
    __tablename__ = "speaking_practices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="hr")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class WritingEvaluation(Base):
    __tablename__ = "writing_evaluations"
    __table_args__ = (
        UniqueConstraint("writing_id", "evaluation_key", name="uq_writing_evaluation_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    writing_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("writing_practices.id"), index=True, nullable=False
    )
    evaluation_key: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False)
    rubric_version: Mapped[str] = mapped_column(String(40), nullable=False)
    evaluation_version: Mapped[str] = mapped_column(String(20), nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dimensions_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    strengths_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    issues_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    suggestions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    already_strong: Mapped[bool] = mapped_column(default=False)
    truncated: Mapped[bool] = mapped_column(default=False)
    truncation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class WritingRewritePreview(Base):
    """Optional coach rewrite — separate from evaluation; never replaces user content."""

    __tablename__ = "writing_rewrite_previews"
    __table_args__ = (
        UniqueConstraint("writing_id", "rewrite_key", name="uq_writing_rewrite_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    writing_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("writing_practices.id"), index=True, nullable=False
    )
    rewrite_key: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False)
    suggested_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    why_better_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    key_changes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    truncated: Mapped[bool] = mapped_column(default=False)
    truncation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class WritingAIRun(Base):
    """Traceability log for writing-related AI invocations. Never stores credentials."""

    __tablename__ = "writing_ai_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    writing_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("writing_practices.id"), index=True, nullable=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    operation: Mapped[str] = mapped_column(String(40), nullable=False, default="evaluate_writing")
    prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    rubric_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


def dumps_json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads_json(raw: str | None, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default
