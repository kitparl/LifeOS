from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Level = Literal["A1", "A2", "B1", "B2", "C1", "C2"]
VocabType = Literal["WORD", "PHRASAL_VERB", "COLLOCATION", "COMMON_EXPRESSION", "FUNCTIONAL_PHRASE"]
SetType = Literal["daily", "manual"]
SetStatus = Literal["active", "accepted"]
DailyState = Literal[
    "NO_ACTIVE_SET", "ACTIVE", "ACCEPTED", "WAITING_FOR_NEXT_MIDNIGHT", "ACTIVE_NEXT_SET"
]


# --------------------------------------------------------------------------
# Vocabulary (master data)
# --------------------------------------------------------------------------

class VocabularyCard(BaseModel):
    """Concise fields for the daily card / list views (PRD §49 — not every field)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    term: str
    type: str
    level: str
    part_of_speech: str
    simple_meaning: str
    example: str
    pronunciation: str | None


class VocabularyDetail(BaseModel):
    """Full field set for the detail screen (PRD §25)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    term: str
    type: str
    level: str
    part_of_speech: str
    simple_meaning: str
    meaning_in_context: str | None
    example: str
    example_context: str | None
    usage_note: str | None
    communication_intents: list[str]
    topics: list[str]
    common_collocations: list[str]
    synonyms: list[str]
    antonyms: list[str]
    commonness: str
    formality: str
    pronunciation: str | None
    learning_priority: str


class VocabularyDetailResponse(BaseModel):
    """VocabularyDetail plus the requesting user's own state for this item."""

    vocabulary: VocabularyDetail
    is_bookmarked: bool
    mastery_level: int
    times_reviewed: int
    example_count: int


# --------------------------------------------------------------------------
# Sets / daily learning
# --------------------------------------------------------------------------

class VocabularySetItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: int
    was_changed: bool
    is_bookmarked: bool = False
    vocabulary: VocabularyCard


class VocabularySetResponse(BaseModel):
    id: str
    set_type: SetType
    set_date: date
    status: SetStatus
    created_at: datetime
    accepted_at: datetime | None
    items: list[VocabularySetItemResponse]


class DailySetResponse(BaseModel):
    state: DailyState
    current_set: VocabularySetResponse | None
    progress_count: int
    progress_total: int
    end_of_dataset: bool


# --------------------------------------------------------------------------
# Progress dashboard
# --------------------------------------------------------------------------

class ProgressResponse(BaseModel):
    vocabulary_learned: int
    total_available_vocabulary: int
    current_level: str | None
    todays_progress_count: int
    todays_progress_total: int
    bookmarks_count: int
    needs_revision_count: int
    current_streak_days: int


# --------------------------------------------------------------------------
# Bookmarks (PRD §23)
# --------------------------------------------------------------------------

class BookmarkResponse(BaseModel):
    id: str
    created_at: datetime
    vocabulary: VocabularyCard


class BookmarkPage(BaseModel):
    items: list[BookmarkResponse]
    total: int


# --------------------------------------------------------------------------
# Personal examples (PRD §24)
# --------------------------------------------------------------------------

class ExampleCreate(BaseModel):
    sentence: str = Field(min_length=1, max_length=2000)
    notes: str | None = Field(default=None, max_length=2000)


class ExampleUpdate(BaseModel):
    sentence: str | None = Field(default=None, min_length=1, max_length=2000)
    notes: str | None = Field(default=None, max_length=2000)


class ExampleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    vocabulary_id: str
    sentence: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# History (PRD §51) / Revision (PRD §21) / Search (PRD §26)
# --------------------------------------------------------------------------

class HistoryEntry(BaseModel):
    set_id: str
    set_date: date
    set_type: SetType
    status: SetStatus
    item_count: int
    items: list[VocabularyCard]


class HistoryPage(BaseModel):
    items: list[HistoryEntry]
    total: int


class VocabularyPage(BaseModel):
    items: list[VocabularyCard]
    total: int


RevisionSource = Literal["today", "previous_day", "date", "all", "bookmarked", "weak", "level", "topic"]


# --------------------------------------------------------------------------
# Games (PRD §28-30)
# --------------------------------------------------------------------------

GameType = Literal[
    "meaning_quiz",
    "synonym_quiz",
    "antonym_quiz",
    "fill_in_blank",
    "example_completion",
    "word_matching",
    "meaning_matching",
]
GameSource = Literal["today", "specific_day", "all_learned", "bookmarked", "needs_revision", "level"]


class GameVocabularyItem(BaseModel):
    """Fuller-than-card shape so the frontend can build any of the 7 game types
    (needs synonyms/antonyms/meaning, not just what fits on a daily card)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    term: str
    type: str
    level: str
    part_of_speech: str
    simple_meaning: str
    example: str
    synonyms: list[str]
    antonyms: list[str]


class GameVocabularyPage(BaseModel):
    items: list[GameVocabularyItem]
    total: int


class GameSessionCreate(BaseModel):
    game_type: GameType
    source: GameSource
    total_questions: int = Field(default=10, ge=1, le=50)
    level: str | None = None
    target_date: date | None = None


class GameSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    game_type: str
    source: str
    total_questions: int
    score: int
    started_at: datetime
    completed_at: datetime | None


class GameAnswerCreate(BaseModel):
    vocabulary_id: str
    question_type: GameType
    is_correct: bool
    user_answer: str | None = Field(default=None, max_length=500)


class GameAnswerResponse(BaseModel):
    id: str
    is_correct: bool
    mastery_level: int


class GameHistoryPage(BaseModel):
    items: list[GameSessionResponse]
    total: int
