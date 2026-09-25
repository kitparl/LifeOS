from datetime import date, datetime

from sqlalchemy import Text, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.modules.communication.vocabulary.models import (
    RESERVED_SEQUENCE_START,
    GameQuestion,
    GameSession,
    UserVocabulary,
    UserVocabularyExample,
    UserVocabularyProgress,
    Vocabulary,
    VocabularyBookmark,
    VocabularyCollection,
    VocabularySet,
    VocabularySetItem,
)

# Rows the daily allocator may hand out. IS NOT TRUE also admits NULL on legacy rows.
_DAILY_ELIGIBLE = Vocabulary.exclude_from_daily.is_not(True)


class VocabularyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Progress (the locked, authoritative pointer)
    # ------------------------------------------------------------------

    async def get_progress_locked(self, user_id: str) -> UserVocabularyProgress | None:
        """Row-lock the user's progress row for the duration of the current transaction.

        Postgres: real row lock (SELECT ... FOR UPDATE). SQLite: the clause is accepted
        but not enforced by the dialect — correctness there relies on SQLite's own
        single-writer semantics plus the UniqueConstraint(user_id, vocabulary_id) backstop
        in allocate_next(). See design doc §3.
        """
        stmt = select(UserVocabularyProgress).where(
            UserVocabularyProgress.user_id == user_id
        ).with_for_update()
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def new_progress(self, user_id: str) -> UserVocabularyProgress:
        progress = UserVocabularyProgress(user_id=user_id, next_sequence_number=1)
        self.db.add(progress)
        return progress

    async def get_progress(self, user_id: str) -> UserVocabularyProgress | None:
        stmt = select(UserVocabularyProgress).where(UserVocabularyProgress.user_id == user_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    # ------------------------------------------------------------------
    # Master vocabulary
    # ------------------------------------------------------------------

    async def get_default_collection(self) -> VocabularyCollection | None:
        stmt = select(VocabularyCollection).order_by(VocabularyCollection.created_at.asc())
        return (await self.db.execute(stmt)).scalars().first()

    async def get_next_unused(self, from_sequence: int, count: int) -> list[Vocabulary]:
        stmt = (
            select(Vocabulary)
            .where(Vocabulary.sequence_number >= from_sequence, _DAILY_ELIGIBLE)
            .order_by(Vocabulary.sequence_number)
            .limit(count)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_vocabulary(self, vocabulary_id: str) -> Vocabulary | None:
        stmt = select(Vocabulary).where(Vocabulary.id == vocabulary_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def count_vocabulary(self) -> int:
        """Daily-eligible rows only: Word Lab saves and Word of the Day rows never inflate the
        "learned / total" denominator, because they can never be allocated."""
        stmt = select(func.count()).select_from(Vocabulary).where(_DAILY_ELIGIBLE)
        return (await self.db.execute(stmt)).scalar_one()

    # ------------------------------------------------------------------
    # Word Lab / Word of the Day rows (never daily-allocated)
    # ------------------------------------------------------------------

    async def find_by_normalized_term(self, normalized_term: str) -> Vocabulary | None:
        """Oldest row whose term matches case-insensitively (dataset rows win over later saves)."""
        stmt = (
            select(Vocabulary)
            .where(func.lower(func.trim(Vocabulary.term)) == normalized_term)
            .order_by(Vocabulary.sequence_number)
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_word_of_the_day(self, day: date) -> Vocabulary | None:
        stmt = select(Vocabulary).where(Vocabulary.wotd_for_date == day)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def next_reserved_sequence_number(self) -> int:
        """Next sequence number in the reserved band above any dataset id (v000001–v999999),
        so future dataset imports can never collide with Word Lab / Word of the Day rows."""
        current = (await self.db.execute(select(func.max(Vocabulary.sequence_number)))).scalar_one()
        return max(current or 0, RESERVED_SEQUENCE_START - 1) + 1

    # ------------------------------------------------------------------
    # Sets
    # ------------------------------------------------------------------

    async def get_latest_set(self, user_id: str) -> VocabularySet | None:
        stmt = (
            select(VocabularySet)
            .where(VocabularySet.user_id == user_id)
            .order_by(VocabularySet.created_at.desc())
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_set(self, set_id: str) -> VocabularySet | None:
        stmt = select(VocabularySet).where(VocabularySet.id == set_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def new_set(self, user_id: str, set_type: str, set_date: date, status: str = "active") -> VocabularySet:
        vset = VocabularySet(user_id=user_id, set_type=set_type, set_date=set_date, status=status)
        self.db.add(vset)
        return vset

    async def get_set_items(self, set_id: str) -> list[VocabularySetItem]:
        stmt = (
            select(VocabularySetItem)
            .where(VocabularySetItem.set_id == set_id)
            .order_by(VocabularySetItem.position)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_set_item(self, set_id: str, position: int) -> VocabularySetItem | None:
        stmt = select(VocabularySetItem).where(
            VocabularySetItem.set_id == set_id, VocabularySetItem.position == position
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def new_set_item(
        self, set_id: str, user_id: str, vocabulary_id: str, sequence_number: int, position: int
    ) -> VocabularySetItem:
        item = VocabularySetItem(
            set_id=set_id,
            user_id=user_id,
            vocabulary_id=vocabulary_id,
            sequence_number=sequence_number,
            position=position,
        )
        self.db.add(item)
        return item

    # ------------------------------------------------------------------
    # User vocabulary (history / no-repeat record)
    # ------------------------------------------------------------------

    def new_user_vocabulary(self, user_id: str, vocabulary_id: str, first_seen_at: datetime) -> UserVocabulary:
        row = UserVocabulary(user_id=user_id, vocabulary_id=vocabulary_id, first_seen_at=first_seen_at)
        self.db.add(row)
        return row

    async def get_user_vocabulary(self, user_id: str, vocabulary_id: str) -> UserVocabulary | None:
        stmt = select(UserVocabulary).where(
            UserVocabulary.user_id == user_id, UserVocabulary.vocabulary_id == vocabulary_id
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def count_learned(self, user_id: str) -> int:
        stmt = select(func.count()).select_from(UserVocabulary).where(
            UserVocabulary.user_id == user_id, UserVocabulary.accepted_at.is_not(None)
        )
        return (await self.db.execute(stmt)).scalar_one()

    async def count_needs_revision(self, user_id: str) -> int:
        stmt = select(func.count()).select_from(UserVocabulary).where(
            UserVocabulary.user_id == user_id,
            UserVocabulary.accepted_at.is_not(None),
            UserVocabulary.mastery_level <= 2,
        )
        return (await self.db.execute(stmt)).scalar_one()

    async def most_recent_learned_level(self, user_id: str) -> str | None:
        stmt = (
            select(Vocabulary.level)
            .join(UserVocabulary, UserVocabulary.vocabulary_id == Vocabulary.id)
            .where(UserVocabulary.user_id == user_id, UserVocabulary.accepted_at.is_not(None))
            .order_by(UserVocabulary.accepted_at.desc())
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def accepted_set_dates(self, user_id: str) -> list[date]:
        """Distinct dates the user accepted a set, most recent first (for streak calc)."""
        stmt = (
            select(VocabularySet.set_date)
            .where(VocabularySet.user_id == user_id, VocabularySet.status == "accepted")
            .distinct()
            .order_by(VocabularySet.set_date.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    # ------------------------------------------------------------------
    # History (sets grouped by date — PRD §51)
    # ------------------------------------------------------------------

    async def list_sets(self, user_id: str, pagination: Pagination) -> tuple[list[VocabularySet], int]:
        stmt = select(VocabularySet).where(VocabularySet.user_id == user_id).order_by(
            VocabularySet.set_date.desc(), VocabularySet.created_at.desc()
        )
        return await paginate(self.db, stmt, pagination)

    # ------------------------------------------------------------------
    # Bookmarks (PRD §23)
    # ------------------------------------------------------------------

    async def get_bookmark(self, user_id: str, vocabulary_id: str) -> VocabularyBookmark | None:
        stmt = select(VocabularyBookmark).where(
            VocabularyBookmark.user_id == user_id, VocabularyBookmark.vocabulary_id == vocabulary_id
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_bookmarked_ids(self, user_id: str, vocabulary_ids: list[str]) -> set[str]:
        if not vocabulary_ids:
            return set()
        stmt = select(VocabularyBookmark.vocabulary_id).where(
            VocabularyBookmark.user_id == user_id,
            VocabularyBookmark.vocabulary_id.in_(vocabulary_ids),
        )
        return set((await self.db.execute(stmt)).scalars().all())

    def new_bookmark(self, user_id: str, vocabulary_id: str) -> VocabularyBookmark:
        bookmark = VocabularyBookmark(user_id=user_id, vocabulary_id=vocabulary_id)
        self.db.add(bookmark)
        return bookmark

    async def delete_bookmark(self, bookmark: VocabularyBookmark) -> None:
        await self.db.delete(bookmark)

    async def list_bookmarks(
        self, user_id: str, pagination: Pagination
    ) -> tuple[list[tuple[VocabularyBookmark, Vocabulary]], int]:
        stmt = (
            select(VocabularyBookmark, Vocabulary)
            .join(Vocabulary, Vocabulary.id == VocabularyBookmark.vocabulary_id)
            .where(VocabularyBookmark.user_id == user_id)
            .order_by(VocabularyBookmark.created_at.desc())
        )
        total = (
            await self.db.execute(
                select(func.count()).select_from(VocabularyBookmark).where(VocabularyBookmark.user_id == user_id)
            )
        ).scalar_one()
        page_stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        rows = (await self.db.execute(page_stmt)).all()
        return [(r[0], r[1]) for r in rows], int(total)

    async def count_bookmarks(self, user_id: str) -> int:
        stmt = select(func.count()).select_from(VocabularyBookmark).where(VocabularyBookmark.user_id == user_id)
        return (await self.db.execute(stmt)).scalar_one()

    # ------------------------------------------------------------------
    # Personal examples (PRD §24 — unlimited, never touch master `example`)
    # ------------------------------------------------------------------

    def new_example(
        self, user_id: str, vocabulary_id: str, sentence: str, notes: str | None
    ) -> UserVocabularyExample:
        example = UserVocabularyExample(user_id=user_id, vocabulary_id=vocabulary_id, sentence=sentence, notes=notes)
        self.db.add(example)
        return example

    async def get_example(self, example_id: str) -> UserVocabularyExample | None:
        stmt = select(UserVocabularyExample).where(UserVocabularyExample.id == example_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def delete_example(self, example: UserVocabularyExample) -> None:
        await self.db.delete(example)

    async def list_examples(self, user_id: str, vocabulary_id: str) -> list[UserVocabularyExample]:
        stmt = (
            select(UserVocabularyExample)
            .where(UserVocabularyExample.user_id == user_id, UserVocabularyExample.vocabulary_id == vocabulary_id)
            .order_by(UserVocabularyExample.created_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def count_examples(self, user_id: str, vocabulary_id: str) -> int:
        stmt = select(func.count()).select_from(UserVocabularyExample).where(
            UserVocabularyExample.user_id == user_id, UserVocabularyExample.vocabulary_id == vocabulary_id
        )
        return (await self.db.execute(stmt)).scalar_one()

    # ------------------------------------------------------------------
    # Search (PRD §26 — indexed LIKE/ILIKE for v1, per requirements Q6)
    # ------------------------------------------------------------------

    async def search_vocabulary(
        self,
        *,
        q: str | None,
        level: str | None,
        type_: str | None,
        part_of_speech: str | None,
        topic: str | None,
        intent: str | None,
        pagination: Pagination,
    ) -> tuple[list[Vocabulary], int]:
        stmt = select(Vocabulary)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Vocabulary.term.ilike(like), Vocabulary.simple_meaning.ilike(like)))
        if level:
            stmt = stmt.where(Vocabulary.level == level)
        if type_:
            stmt = stmt.where(Vocabulary.type == type_)
        if part_of_speech:
            stmt = stmt.where(Vocabulary.part_of_speech == part_of_speech)
        if topic:
            # Portable substring match on the JSON-serialized list — adequate for single-word
            # topic tags at this dataset size (Q6: keep v1 search simple/portable).
            stmt = stmt.where(func.cast(Vocabulary.topics, Text).ilike(f"%{topic}%"))
        if intent:
            stmt = stmt.where(
                func.cast(Vocabulary.communication_intents, Text).ilike(f"%{intent}%")
            )
        stmt = stmt.order_by(Vocabulary.sequence_number)
        return await paginate(self.db, stmt, pagination)

    # ------------------------------------------------------------------
    # Revision (PRD §21 — reuses learned vocabulary, never allocates)
    # ------------------------------------------------------------------

    async def get_revision_vocabulary(
        self,
        user_id: str,
        *,
        source: str,
        target_date: date | None,
        level: str | None,
        topic: str | None,
        pagination: Pagination,
    ) -> tuple[list[Vocabulary], int]:
        stmt = (
            select(Vocabulary)
            .join(UserVocabulary, UserVocabulary.vocabulary_id == Vocabulary.id)
            .where(UserVocabulary.user_id == user_id, UserVocabulary.accepted_at.is_not(None))
        )

        if source == "date" and target_date is not None:
            stmt = stmt.join(
                VocabularySetItem,
                and_(
                    VocabularySetItem.vocabulary_id == Vocabulary.id,
                    VocabularySetItem.user_id == user_id,
                ),
            ).join(VocabularySet, VocabularySet.id == VocabularySetItem.set_id).where(
                VocabularySet.set_date == target_date
            )
        elif source == "bookmarked":
            stmt = stmt.join(
                VocabularyBookmark,
                and_(
                    VocabularyBookmark.vocabulary_id == Vocabulary.id,
                    VocabularyBookmark.user_id == user_id,
                ),
            )
        elif source == "weak":
            stmt = stmt.where(UserVocabulary.mastery_level <= 2)
        elif source == "level" and level:
            stmt = stmt.where(Vocabulary.level == level)
        elif source == "topic" and topic:
            stmt = stmt.where(func.cast(Vocabulary.topics, Text).ilike(f"%{topic}%"))
        # source == "all" (or anything else): every learned item, no extra filter.

        stmt = stmt.order_by(Vocabulary.sequence_number)
        return await paginate(self.db, stmt, pagination)

    # ------------------------------------------------------------------
    # Games (PRD §28-29 — reuse learned vocabulary, never allocate)
    # ------------------------------------------------------------------

    def new_game_session(
        self,
        user_id: str,
        game_type: str,
        source: str,
        total_questions: int,
        *,
        selected_level: str | None = None,
        selected_date: date | None = None,
    ) -> GameSession:
        session = GameSession(
            user_id=user_id,
            game_type=game_type,
            source=source,
            selected_level=selected_level,
            selected_date=selected_date,
            total_questions=total_questions,
        )
        self.db.add(session)
        return session

    async def get_game_session(self, session_id: str) -> GameSession | None:
        stmt = select(GameSession).where(GameSession.id == session_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def new_game_question(
        self,
        session_id: str,
        user_id: str,
        vocabulary_id: str,
        question_type: str,
        is_correct: bool,
        user_answer: str | None,
        answered_at: datetime,
    ) -> GameQuestion:
        question = GameQuestion(
            session_id=session_id,
            user_id=user_id,
            vocabulary_id=vocabulary_id,
            question_type=question_type,
            is_correct=is_correct,
            user_answer=user_answer,
            answered_at=answered_at,
        )
        self.db.add(question)
        return question

    async def list_game_sessions(self, user_id: str, pagination: Pagination) -> tuple[list[GameSession], int]:
        stmt = (
            select(GameSession)
            .where(GameSession.user_id == user_id, GameSession.completed_at.is_not(None))
            .order_by(GameSession.completed_at.desc())
        )
        return await paginate(self.db, stmt, pagination)
