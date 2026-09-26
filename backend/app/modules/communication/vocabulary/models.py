"""Vocabulary Learning & Communication Module — ORM models.

Lives under ``app.modules.communication.vocabulary`` (replaces the earlier free-form
``VocabularyWord`` notebook feature). Owns the structured master vocabulary dataset and
each user's independent progression through it.
"""

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, new_id
from app.core.timezone import utc_now

LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
VOCAB_TYPES = ("WORD", "PHRASAL_VERB", "COLLOCATION", "COMMON_EXPRESSION", "FUNCTIONAL_PHRASE")
COMMONNESS = ("very_common", "common", "less_common", "advanced")
FORMALITY = ("formal", "neutral", "informal")
LEARNING_PRIORITY = ("low", "medium", "high")
SET_TYPES = ("daily", "manual")
SET_STATUSES = ("active", "accepted")
GAME_TYPES = (
    "meaning_quiz",
    "synonym_quiz",
    "antonym_quiz",
    "fill_in_blank",
    "example_completion",
    "word_matching",
    "meaning_matching",
)
# Where a vocabulary row came from. Only "dataset" rows feed daily allocation by default.
SOURCE_DATASET = "dataset"
SOURCE_API = "api"
SOURCE_USER_SAVED = "user_saved"
SOURCES = (SOURCE_DATASET, SOURCE_API, SOURCE_USER_SAVED)
# Dataset ids are v000001–v999999 (sequence 1–999999). Non-dataset rows are numbered from here up.
RESERVED_SEQUENCE_START = 1_000_000_000
GAME_SOURCES = ("today", "specific_day", "all_learned", "bookmarked", "needs_revision", "level")




class VocabularyCollection(Base):
    __tablename__ = "vocabulary_collections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Vocabulary(Base):
    """Master dataset row. ``id`` preserves the source dataset's stable string id
    (e.g. "v000001") — never regenerated, never renumbered (PRD §7/§9/§17)."""

    __tablename__ = "vocabulary"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    collection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vocabulary_collections.id"), index=True, nullable=False
    )
    # Parsed from the numeric suffix of `id` at import time. This — not the string id — is
    # what the sequence allocator orders/filters on.
    sequence_number: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    term: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    level: Mapped[str] = mapped_column(String(4), index=True, nullable=False)
    part_of_speech: Mapped[str] = mapped_column(String(32), nullable=False)
    simple_meaning: Mapped[str] = mapped_column(Text, nullable=False)
    meaning_in_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    communication_intents: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    topics: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    example: Mapped[str] = mapped_column(Text, nullable=False)
    example_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    common_collocations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    synonyms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    antonyms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    commonness: Mapped[str] = mapped_column(String(16), nullable=False)
    formality: Mapped[str] = mapped_column(String(16), nullable=False)
    pronunciation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    learning_priority: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    dataset_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    source: Mapped[str] = mapped_column(String(16), nullable=False, default=SOURCE_DATASET)
    # True for Word Lab saves and Word of the Day rows: allocate_next must never hand them out.
    exclude_from_daily: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Set on the row that is the Word of the Day for this IST date (unique index; see migrations).
    wotd_for_date: Mapped[date | None] = mapped_column(Date, nullable=True, unique=True, index=True)


class UserVocabularyProgress(Base):
    """One authoritative pointer per user (PRD §10). Locked via with_for_update() during
    allocation — see vocabulary/sequencing.py::allocate_next."""

    __tablename__ = "user_vocabulary_progress"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_vocabulary_progress_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    next_sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active_set_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("vocabulary_sets.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class VocabularySet(Base):
    __tablename__ = "vocabulary_sets"
    __table_args__ = (UniqueConstraint("id", name="uq_vocabulary_sets_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    set_type: Mapped[str] = mapped_column(String(8), nullable=False)
    set_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(8), index=True, nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VocabularySetItem(Base):
    __tablename__ = "vocabulary_set_items"
    __table_args__ = (UniqueConstraint("set_id", "position", name="uq_set_item_position"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    set_id: Mapped[str] = mapped_column(String(36), ForeignKey("vocabulary_sets.id"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    vocabulary_id: Mapped[str] = mapped_column(String(16), ForeignKey("vocabulary.id"), index=True, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    was_changed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class UserVocabulary(Base):
    """The no-repeat backstop AND the learning-history/mastery record (PRD §20, §22).
    Exactly one row per (user_id, vocabulary_id), created once at allocation time."""

    __tablename__ = "user_vocabulary"
    __table_args__ = (UniqueConstraint("user_id", "vocabulary_id", name="uq_user_vocabulary"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    vocabulary_id: Mapped[str] = mapped_column(String(16), ForeignKey("vocabulary.id"), index=True, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    times_reviewed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    times_incorrect: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mastery_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_interval: Mapped[int | None] = mapped_column(Integer, nullable=True)
    repetition_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class VocabularyBookmark(Base):
    __tablename__ = "vocabulary_bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "vocabulary_id", name="uq_vocabulary_bookmark"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    vocabulary_id: Mapped[str] = mapped_column(String(16), ForeignKey("vocabulary.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=utc_now)


class UserVocabularyExample(Base):
    __tablename__ = "user_vocabulary_examples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    vocabulary_id: Mapped[str] = mapped_column(String(16), ForeignKey("vocabulary.id"), index=True, nullable=False)
    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    game_type: Mapped[str] = mapped_column(String(24), nullable=False)
    source: Mapped[str] = mapped_column(String(24), nullable=False)
    selected_level: Mapped[str | None] = mapped_column(String(4), nullable=True)
    selected_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GameQuestion(Base):
    __tablename__ = "game_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("game_sessions.id"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    vocabulary_id: Mapped[str] = mapped_column(String(16), ForeignKey("vocabulary.id"), index=True, nullable=False)
    question_type: Mapped[str] = mapped_column(String(24), nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
