from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError, get_or_404
from app.core.pagination import Pagination
from app.core.timezone import ist_today, utc_now
from app.modules.auth.models import User
from app.modules.communication.vocabulary.mastery import next_mastery_level
from app.modules.communication.vocabulary.models import VocabularySet
from app.modules.communication.vocabulary.repository import VocabularyRepository
from app.modules.communication.vocabulary.schemas import (
    BookmarkPage,
    BookmarkResponse,
    DailySetResponse,
    ExampleCreate,
    ExampleResponse,
    ExampleUpdate,
    GameAnswerCreate,
    GameAnswerResponse,
    GameHistoryPage,
    GameSessionCreate,
    GameSessionResponse,
    GameVocabularyItem,
    GameVocabularyPage,
    HistoryEntry,
    HistoryPage,
    ProgressResponse,
    VocabularyCard,
    VocabularyDetail,
    VocabularyDetailResponse,
    VocabularyPage,
    VocabularySetItemResponse,
    VocabularySetResponse,
)
from app.modules.communication.vocabulary.sequencing import allocate_next, create_set, resolve_daily_state

# Game sources (PRD §28) map onto the same underlying learned-vocabulary query as
# revision sources (PRD §21) — reused rather than duplicated (PRD §3).
_GAME_SOURCE_TO_REVISION_SOURCE = {
    "today": "today",
    "specific_day": "date",
    "all_learned": "all",
    "bookmarked": "bookmarked",
    "needs_revision": "weak",
    "level": "level",
}



async def _set_response(repo: VocabularyRepository, vset: VocabularySet, user_id: str) -> VocabularySetResponse:
    items = await repo.get_set_items(vset.id)
    bookmarked_ids = await repo.list_bookmarked_ids(user_id, [item.vocabulary_id for item in items])
    item_responses: list[VocabularySetItemResponse] = []
    for item in items:
        vocab = await repo.get_vocabulary(item.vocabulary_id)
        if vocab is None:
            continue
        item_responses.append(
            VocabularySetItemResponse(
                position=item.position,
                was_changed=item.was_changed,
                is_bookmarked=item.vocabulary_id in bookmarked_ids,
                vocabulary=VocabularyCard.model_validate(vocab),
            )
        )
    return VocabularySetResponse(
        id=vset.id,
        set_type=vset.set_type,
        set_date=vset.set_date,
        status=vset.status,
        created_at=vset.created_at,
        accepted_at=vset.accepted_at,
        items=item_responses,
    )


class VocabularyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = VocabularyRepository(db)

    async def get_daily_set(self, user: User) -> DailySetResponse:
        result = await resolve_daily_state(self.db, self.repo, user)
        current = await _set_response(self.repo, result.current_set, user.id) if result.current_set else None
        total = len(current.items) if current else 0
        count = total if (current and current.status == "accepted") else 0
        return DailySetResponse(
            state=result.state,
            current_set=current,
            progress_count=count,
            progress_total=total,
            end_of_dataset=result.end_of_dataset,
        )

    async def _get_owned_set(self, user: User, set_id: str) -> VocabularySet:
        vset = await self.repo.get_set(set_id)
        if vset is None or vset.user_id != user.id:
            raise NotFoundError("Vocabulary set not found")  # never leak cross-user existence
        return vset

    async def accept_current_set(self, user: User, set_id: str) -> VocabularySetResponse:
        vset = await self._get_owned_set(user, set_id)
        if vset.status != "active":
            raise ConflictError("This set is not active and cannot be accepted")

        now = utc_now()
        vset.status = "accepted"
        vset.accepted_at = now

        items = await self.repo.get_set_items(vset.id)
        for item in items:
            uv = await self.repo.get_user_vocabulary(user.id, item.vocabulary_id)
            if uv is not None:
                uv.accepted_at = now

        await self.db.flush()
        return await _set_response(self.repo, vset, user.id)

    async def change_vocabulary_item(self, user: User, set_id: str, position: int) -> VocabularySetResponse:
        vset = await self._get_owned_set(user, set_id)
        if vset.status != "active":
            raise ConflictError("Only items in an active (not yet accepted) set can be changed")

        item = get_or_404(await self.repo.get_set_item(set_id, position), "Set item not found")

        new_rows = await allocate_next(self.db, self.repo, user, 1)
        if not new_rows:
            raise ConflictError("No more unused vocabulary available to change into")
        new_vocab = new_rows[0]

        item.vocabulary_id = new_vocab.id
        item.sequence_number = new_vocab.sequence_number
        item.was_changed = True
        await self.db.flush()
        return await _set_response(self.repo, vset, user.id)

    async def get_next_set(self, user: User) -> VocabularySetResponse:
        latest = await self.repo.get_latest_set(user.id)
        if latest is None or latest.status != "accepted":
            raise ConflictError("Accept the current set before requesting the next one")

        vset = await create_set(self.db, self.repo, user, "manual")
        if vset is None:
            raise ConflictError("No more unused vocabulary available")
        return await _set_response(self.repo, vset, user.id)

    # ------------------------------------------------------------------
    # Vocabulary detail (PRD §25)
    # ------------------------------------------------------------------

    async def get_vocabulary_detail(self, user: User, vocabulary_id: str) -> VocabularyDetailResponse:
        vocab = get_or_404(await self.repo.get_vocabulary(vocabulary_id), "Vocabulary not found")
        bookmark = await self.repo.get_bookmark(user.id, vocabulary_id)
        uv = await self.repo.get_user_vocabulary(user.id, vocabulary_id)
        example_count = await self.repo.count_examples(user.id, vocabulary_id)
        return VocabularyDetailResponse(
            vocabulary=VocabularyDetail.model_validate(vocab),
            is_bookmarked=bookmark is not None,
            mastery_level=uv.mastery_level if uv else 0,
            times_reviewed=uv.times_reviewed if uv else 0,
            example_count=example_count,
        )

    # ------------------------------------------------------------------
    # Bookmarks (PRD §23 — never affect sequence)
    # ------------------------------------------------------------------

    async def bookmark_vocabulary(self, user: User, vocabulary_id: str) -> BookmarkResponse:
        get_or_404(await self.repo.get_vocabulary(vocabulary_id), "Vocabulary not found")
        existing = await self.repo.get_bookmark(user.id, vocabulary_id)
        bookmark = existing or self.repo.new_bookmark(user.id, vocabulary_id)
        await self.db.flush()
        vocab = await self.repo.get_vocabulary(vocabulary_id)
        return BookmarkResponse(
            id=bookmark.id, created_at=bookmark.created_at, vocabulary=VocabularyCard.model_validate(vocab)
        )

    async def remove_bookmark(self, user: User, vocabulary_id: str) -> None:
        bookmark = await self.repo.get_bookmark(user.id, vocabulary_id)
        if bookmark is not None:
            await self.repo.delete_bookmark(bookmark)
            await self.db.flush()
        # Removing a bookmark never touches user_vocabulary — learning history is preserved.

    async def get_bookmarks(self, user: User, pagination: Pagination) -> BookmarkPage:
        rows, total = await self.repo.list_bookmarks(user.id, pagination)
        return BookmarkPage(
            items=[
                BookmarkResponse(id=b.id, created_at=b.created_at, vocabulary=VocabularyCard.model_validate(v))
                for b, v in rows
            ],
            total=total,
        )

    # ------------------------------------------------------------------
    # Personal examples (PRD §24 — unlimited, never overwrite the master example)
    # ------------------------------------------------------------------

    async def add_personal_example(self, user: User, vocabulary_id: str, payload: ExampleCreate) -> ExampleResponse:
        get_or_404(await self.repo.get_vocabulary(vocabulary_id), "Vocabulary not found")
        example = self.repo.new_example(user.id, vocabulary_id, payload.sentence, payload.notes)
        await self.db.flush()
        return ExampleResponse.model_validate(example)

    async def _get_owned_example(self, user: User, example_id: str):
        example = get_or_404(await self.repo.get_example(example_id), "Example not found")
        if example.user_id != user.id:
            raise NotFoundError("Example not found")
        return example

    async def update_personal_example(
        self, user: User, example_id: str, payload: ExampleUpdate
    ) -> ExampleResponse:
        example = await self._get_owned_example(user, example_id)
        if payload.sentence is not None:
            example.sentence = payload.sentence
        if payload.notes is not None:
            example.notes = payload.notes
        await self.db.flush()
        return ExampleResponse.model_validate(example)

    async def delete_personal_example(self, user: User, example_id: str) -> None:
        example = await self._get_owned_example(user, example_id)
        await self.repo.delete_example(example)
        await self.db.flush()

    async def list_personal_examples(self, user: User, vocabulary_id: str) -> list[ExampleResponse]:
        examples = await self.repo.list_examples(user.id, vocabulary_id)
        return [ExampleResponse.model_validate(e) for e in examples]

    # ------------------------------------------------------------------
    # History (PRD §51 — grouped by date, reflects what was actually shown)
    # ------------------------------------------------------------------

    async def get_history(self, user: User, pagination: Pagination) -> HistoryPage:
        sets, total = await self.repo.list_sets(user.id, pagination)
        entries: list[HistoryEntry] = []
        for vset in sets:
            items = await self.repo.get_set_items(vset.id)
            cards = []
            for item in items:
                vocab = await self.repo.get_vocabulary(item.vocabulary_id)
                if vocab is not None:
                    cards.append(VocabularyCard.model_validate(vocab))
            entries.append(
                HistoryEntry(
                    set_id=vset.id,
                    set_date=vset.set_date,
                    set_type=vset.set_type,
                    status=vset.status,
                    item_count=len(cards),
                    items=cards,
                )
            )
        return HistoryPage(items=entries, total=total)

    # ------------------------------------------------------------------
    # Progress dashboard (PRD §52 — no hard-coded denominator)
    # ------------------------------------------------------------------

    async def get_progress(self, user: User) -> ProgressResponse:
        daily = await self.get_daily_set(user)
        learned = await self.repo.count_learned(user.id)
        total_available = await self.repo.count_vocabulary()
        current_level = await self.repo.most_recent_learned_level(user.id)
        bookmarks_count = await self.repo.count_bookmarks(user.id)
        needs_revision = await self.repo.count_needs_revision(user.id)
        streak = await self._current_streak_days(user.id)
        return ProgressResponse(
            vocabulary_learned=learned,
            total_available_vocabulary=total_available,
            current_level=current_level,
            todays_progress_count=daily.progress_count,
            todays_progress_total=daily.progress_total,
            bookmarks_count=bookmarks_count,
            needs_revision_count=needs_revision,
            current_streak_days=streak,
        )

    async def _current_streak_days(self, user_id: str) -> int:
        dates = await self.repo.accepted_set_dates(user_id)
        if not dates:
            return 0
        today = ist_today()
        if dates[0] < today - timedelta(days=1):
            return 0  # most recent acceptance is more than a day old — streak broken
        streak = 0
        expected = dates[0]
        for d in dates:
            if d == expected:
                streak += 1
                expected = d - timedelta(days=1)
            else:
                break
        return streak

    # ------------------------------------------------------------------
    # Search (PRD §26)
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
    ) -> VocabularyPage:
        rows, total = await self.repo.search_vocabulary(
            q=q,
            level=level,
            type_=type_,
            part_of_speech=part_of_speech,
            topic=topic,
            intent=intent,
            pagination=pagination,
        )
        return VocabularyPage(items=[VocabularyCard.model_validate(v) for v in rows], total=total)

    # ------------------------------------------------------------------
    # Revision (PRD §21 — reuses learned vocabulary, never advances the sequence)
    # ------------------------------------------------------------------

    def _resolve_revision_query(
        self, source: str, target_date: date | None, level: str | None, topic: str | None
    ) -> tuple[str, date | None]:
        if source == "today":
            return "date", ist_today()
        if source == "previous_day":
            return "date", ist_today() - timedelta(days=1)
        if source == "date" and target_date is None:
            raise BadRequestError("source=date requires a date parameter")
        if source == "level" and not level:
            raise BadRequestError("source=level requires a level parameter")
        if source == "topic" and not topic:
            raise BadRequestError("source=topic requires a topic parameter")
        return source, target_date

    async def get_revision_vocabulary(
        self,
        user: User,
        *,
        source: str,
        target_date: date | None,
        level: str | None,
        topic: str | None,
        pagination: Pagination,
    ) -> VocabularyPage:
        resolved_source, resolved_date = self._resolve_revision_query(source, target_date, level, topic)
        rows, total = await self.repo.get_revision_vocabulary(
            user.id,
            source=resolved_source,
            target_date=resolved_date,
            level=level,
            topic=topic,
            pagination=pagination,
        )
        return VocabularyPage(items=[VocabularyCard.model_validate(v) for v in rows], total=total)

    # ------------------------------------------------------------------
    # Games (PRD §28-30 — reuse learned vocabulary, never advance the sequence)
    # ------------------------------------------------------------------

    async def get_game_vocabulary(
        self,
        user: User,
        *,
        source: str,
        level: str | None,
        target_date: date | None,
        pagination: Pagination,
    ) -> GameVocabularyPage:
        if source not in _GAME_SOURCE_TO_REVISION_SOURCE:
            raise BadRequestError(f"Unknown game source: {source}")
        revision_source = _GAME_SOURCE_TO_REVISION_SOURCE[source]
        resolved_source, resolved_date = self._resolve_revision_query(revision_source, target_date, level, None)
        rows, total = await self.repo.get_revision_vocabulary(
            user.id,
            source=resolved_source,
            target_date=resolved_date,
            level=level,
            topic=None,
            pagination=pagination,
        )
        return GameVocabularyPage(items=[GameVocabularyItem.model_validate(v) for v in rows], total=total)

    async def create_game_session(self, user: User, payload: GameSessionCreate) -> GameSessionResponse:
        if payload.source not in _GAME_SOURCE_TO_REVISION_SOURCE:
            raise BadRequestError(f"Unknown game source: {payload.source}")
        session = self.repo.new_game_session(
            user.id,
            payload.game_type,
            payload.source,
            payload.total_questions,
            selected_level=payload.level,
            selected_date=payload.target_date,
        )
        await self.db.flush()
        return GameSessionResponse.model_validate(session)

    async def _get_owned_session(self, user: User, session_id: str):
        session = get_or_404(await self.repo.get_game_session(session_id), "Game session not found")
        if session.user_id != user.id:
            raise NotFoundError("Game session not found")
        return session

    async def submit_game_answer(
        self, user: User, session_id: str, payload: GameAnswerCreate
    ) -> GameAnswerResponse:
        session = await self._get_owned_session(user, session_id)
        if session.completed_at is not None:
            raise ConflictError("This game session is already completed")

        now = utc_now()
        question = self.repo.new_game_question(
            session.id, user.id, payload.vocabulary_id, payload.question_type,
            payload.is_correct, payload.user_answer, now,
        )

        mastery_level = 0
        uv = await self.repo.get_user_vocabulary(user.id, payload.vocabulary_id)
        if uv is not None:
            uv.times_reviewed += 1
            if payload.is_correct:
                uv.times_correct += 1
            else:
                uv.times_incorrect += 1
            uv.mastery_level = next_mastery_level(uv.mastery_level, payload.is_correct)
            uv.last_reviewed_at = now
            mastery_level = uv.mastery_level

        if payload.is_correct:
            session.score += 1

        await self.db.flush()
        return GameAnswerResponse(id=question.id, is_correct=payload.is_correct, mastery_level=mastery_level)

    async def complete_game_session(self, user: User, session_id: str) -> GameSessionResponse:
        session = await self._get_owned_session(user, session_id)
        if session.completed_at is None:
            session.completed_at = utc_now()
            await self.db.flush()
        return GameSessionResponse.model_validate(session)

    async def get_game_history(self, user: User, pagination: Pagination) -> GameHistoryPage:
        sessions, total = await self.repo.list_game_sessions(user.id, pagination)
        return GameHistoryPage(items=[GameSessionResponse.model_validate(s) for s in sessions], total=total)
