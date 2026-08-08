import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

LEARNING_TYPES = ("book", "course", "video", "coding", "interview_prep", "study_plan")
LEARNING_STATUSES = ("planned", "in_progress", "completed", "paused")
TRACK_STATUSES = ("planned", "active", "completed", "paused")
RESOURCE_TYPES = ("video", "playlist", "article", "docs", "course", "paper", "repo", "book")
RESOURCE_PRIORITY = ("primary", "supporting", "optional")


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LearningTrack(Base):
    __tablename__ = "learning_tracks"
    __table_args__ = (UniqueConstraint("user_id", "slug", name="uq_learning_track_user_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="planned")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    weekly_hours_target: Mapped[int] = mapped_column(Integer, nullable=False, default=11)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    phases: Mapped[list["LearningItem"]] = relationship(
        "LearningItem",
        back_populates="track",
        cascade="all, delete-orphan",
        order_by="LearningItem.sort_order",
        foreign_keys="LearningItem.track_id",
    )


class LearningItem(Base):
    __tablename__ = "learning_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    track_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("learning_tracks.id", ondelete="CASCADE"), index=True, nullable=True
    )
    slug: Mapped[str | None] = mapped_column(String(64), nullable=True)
    item_type: Mapped[str] = mapped_column(String(32), nullable=False, default="book")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(120), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="planned")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    track: Mapped["LearningTrack | None"] = relationship(
        "LearningTrack", back_populates="phases", foreign_keys=[track_id]
    )
    concepts: Mapped[list["LearningConcept"]] = relationship(
        "LearningConcept",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="LearningConcept.sort_order",
    )
    # Phase-level resources only; concept-level rows also carry item_id.
    resources: Mapped[list["LearningResource"]] = relationship(
        "LearningResource",
        primaryjoin=(
            "and_(LearningItem.id == LearningResource.item_id, "
            "LearningResource.concept_id.is_(None))"
        ),
        order_by="LearningResource.sort_order",
        viewonly=True,
    )


class LearningConcept(Base):
    __tablename__ = "learning_concepts"
    __table_args__ = (UniqueConstraint("item_id", "slug", name="uq_learning_concept_item_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("learning_items.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    week_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    can_explain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failure_modes_known: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tradeoffs_known: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    artifact_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    item: Mapped["LearningItem"] = relationship("LearningItem", back_populates="concepts")
    resources: Mapped[list["LearningResource"]] = relationship(
        "LearningResource",
        back_populates="concept",
        cascade="all, delete-orphan",
        order_by="LearningResource.sort_order",
        foreign_keys="LearningResource.concept_id",
    )
    sessions: Mapped[list["StudySession"]] = relationship(
        "StudySession",
        back_populates="concept",
        cascade="all, delete-orphan",
        foreign_keys="StudySession.concept_id",
    )
    notes: Mapped[list["LearningConceptNote"]] = relationship(
        "LearningConceptNote",
        back_populates="concept",
        cascade="all, delete-orphan",
        foreign_keys="LearningConceptNote.concept_id",
    )


class LearningConceptNote(Base):
    """Links a concept to a knowledge_notes section so deep notes live in one place."""

    __tablename__ = "learning_concept_notes"
    __table_args__ = (
        UniqueConstraint("concept_id", "section_id", name="uq_learning_concept_note"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    concept_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("learning_concepts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    section_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_sections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    concept: Mapped["LearningConcept"] = relationship("LearningConcept", back_populates="notes")


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    item_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("learning_items.id", ondelete="CASCADE"), index=True, nullable=True
    )
    concept_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("learning_concepts.id", ondelete="CASCADE"), index=True, nullable=True
    )
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False, default="article")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(120), nullable=True)
    author: Mapped[str | None] = mapped_column(String(120), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="supporting")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_consumed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_verified_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    concept: Mapped["LearningConcept | None"] = relationship(
        "LearningConcept", back_populates="resources", foreign_keys=[concept_id]
    )


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("learning_items.id", ondelete="CASCADE"), index=True, nullable=False
    )
    concept_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("learning_concepts.id", ondelete="SET NULL"), index=True, nullable=True
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    can_explain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    artifact_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    concept: Mapped["LearningConcept | None"] = relationship(
        "LearningConcept", back_populates="sessions", foreign_keys=[concept_id]
    )
