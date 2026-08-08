from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge_notes.repository import KnowledgeNotesRepository
from app.modules.knowledge_notes.schemas import ChapterCreate, SectionCreate, SubjectCreate
from app.modules.learning.models import LearningItem
from app.modules.learning.repository import LearningRepository
from app.modules.learning.schemas import (
    ConceptListItem,
    ConceptNoteCreate,
    ConceptNoteResponse,
    ConceptResponse,
    ConceptUpdate,
    LearningCreate,
    LearningListItem,
    LearningResponse,
    LearningUpdate,
    ResourceCreate,
    ResourceResponse,
    ResourceUpdate,
    SessionCreate,
    SessionResponse,
    SessionStats,
    TrackCreate,
    TrackDetail,
    TrackListItem,
    TrackProgress,
)


def _study_streak(dates: list[date]) -> int:
    if not dates:
        return 0
    unique = sorted(set(dates), reverse=True)
    today = date.today()
    if unique[0] not in (today, today - timedelta(days=1)):
        return 0
    streak = 1
    expected = unique[0] - timedelta(days=1)
    for d in unique[1:]:
        if d == expected:
            streak += 1
            expected = d - timedelta(days=1)
        elif d < expected:
            break
    return streak


class LearningService:
    def __init__(self, db: AsyncSession):
        self.repo = LearningRepository(db)
        self.db = db

    # --- Legacy items ---

    async def list_items(self, user_id: str, item_type: str | None = None) -> list[LearningListItem]:
        items = await self.repo.list_items(user_id, item_type)
        return [LearningListItem.model_validate(i) for i in items]

    async def get_item(self, user_id: str, item_id: str) -> LearningResponse:
        item = await self.repo.get_by_id(user_id, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning item not found")
        return LearningResponse.model_validate(item)

    async def create_item(self, user_id: str, data: LearningCreate) -> LearningResponse:
        item = await self.repo.create(user_id, data)
        return LearningResponse.model_validate(item)

    async def update_item(self, user_id: str, item_id: str, data: LearningUpdate) -> LearningResponse:
        item = await self.repo.get_by_id(user_id, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning item not found")
        patch = data
        if data.progress is None and data.status == "completed":
            patch = data.model_copy(update={"progress": 100})
        updated = await self.repo.update(item, patch)
        return LearningResponse.model_validate(updated)

    async def delete_item(self, user_id: str, item_id: str) -> None:
        item = await self.repo.get_by_id(user_id, item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning item not found")
        await self.repo.delete(item)

    # --- Tracks ---

    async def list_tracks(self, user_id: str) -> list[TrackListItem]:
        tracks = await self.repo.list_tracks(user_id)
        return [TrackListItem.model_validate(t) for t in tracks]

    async def create_track(self, user_id: str, data: TrackCreate) -> TrackListItem:
        existing = await self.repo.get_track_by_slug(user_id, data.slug)
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, "Track slug already exists")
        track = await self.repo.create_track(user_id, data)
        return TrackListItem.model_validate(track)

    async def get_track(self, user_id: str, track_id: str) -> TrackDetail:
        track = await self.repo.get_track(user_id, track_id)
        if not track:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Track not found")
        return TrackDetail.model_validate(track)

    async def track_progress(self, user_id: str, track_id: str) -> TrackProgress:
        track = await self.repo.get_track(user_id, track_id)
        if not track:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Track not found")
        total, gated = await self.repo.count_concepts_for_track(track_id)
        percent = round(100 * gated / total, 1) if total else 0.0
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        minutes_week = await self.repo.sum_session_minutes(
            user_id, from_date=week_start, to_date=today, track_id=track_id
        )
        minutes_total = await self.repo.sum_session_minutes(user_id, track_id=track_id)
        streak = _study_streak(await self.repo.session_dates(user_id))
        return TrackProgress(
            track_id=track_id,
            percent_complete=percent,
            concepts_total=total,
            concepts_gated=gated,
            hours_logged=round(minutes_total / 60, 2),
            weekly_hours_target=track.weekly_hours_target,
            pace_hours_this_week=round(minutes_week / 60, 2),
            study_streak_days=streak,
        )

    # --- Concepts ---

    async def list_concepts(
        self, user_id: str, item_id: str | None = None, week: int | None = None
    ) -> list[ConceptListItem]:
        concepts = await self.repo.list_concepts(user_id, item_id, week)
        return [ConceptListItem.model_validate(c) for c in concepts]

    async def get_concept(self, user_id: str, concept_id: str) -> ConceptResponse:
        concept = await self.repo.get_concept(user_id, concept_id)
        if not concept:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Concept not found")
        return await self._concept_with_inherited(user_id, concept)

    async def _concept_with_inherited(self, user_id: str, concept) -> ConceptResponse:
        """Phase-level resources apply to every concept in the phase, so surface them here."""
        response = ConceptResponse.model_validate(concept)
        phase_rows = await self.repo.list_resources(user_id, item_id=concept.item_id)
        response.inherited_resources = [
            ResourceResponse.model_validate(r) for r in phase_rows if r.concept_id is None
        ]
        return response

    async def update_concept(
        self, user_id: str, concept_id: str, data: ConceptUpdate
    ) -> ConceptResponse:
        concept = await self.repo.get_concept(user_id, concept_id)
        if not concept:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Concept not found")
        updated = await self.repo.update_concept(concept, data)
        await self._rollup_item_progress(updated.item_id)
        # reload with resources
        reloaded = await self.repo.get_concept(user_id, concept_id)
        return await self._concept_with_inherited(user_id, reloaded)

    async def _rollup_item_progress(self, item_id: str) -> None:
        total, gated = await self.repo.count_concepts_for_item(item_id)
        if total == 0:
            return
        item = await self.db.get(LearningItem, item_id)
        if item is None:
            return
        item.progress = round(100 * gated / total)
        await self.db.flush()

    # --- Resources ---

    async def list_resources(
        self, user_id: str, concept_id: str | None = None, item_id: str | None = None
    ) -> list[ResourceResponse]:
        rows = await self.repo.list_resources(user_id, concept_id, item_id)
        return [ResourceResponse.model_validate(r) for r in rows]

    async def create_resource(self, user_id: str, data: ResourceCreate) -> ResourceResponse:
        if not data.concept_id and not data.item_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "concept_id or item_id required")
        if data.concept_id:
            concept = await self.repo.get_concept(user_id, data.concept_id)
            if not concept:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Concept not found")
            if not data.item_id:
                data = data.model_copy(update={"item_id": concept.item_id})
        elif data.item_id:
            item = await self.repo.get_by_id(user_id, data.item_id)
            if not item:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning item not found")
        resource = await self.repo.create_resource(user_id, data)
        return ResourceResponse.model_validate(resource)

    async def update_resource(
        self, user_id: str, resource_id: str, data: ResourceUpdate
    ) -> ResourceResponse:
        resource = await self.repo.get_resource(user_id, resource_id)
        if not resource:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Resource not found")
        updated = await self.repo.update_resource(resource, data)
        return ResourceResponse.model_validate(updated)

    # --- Sessions ---

    async def list_sessions(
        self, user_id: str, from_date: date | None = None, to_date: date | None = None
    ) -> list[SessionResponse]:
        rows = await self.repo.list_sessions(user_id, from_date, to_date)
        return [SessionResponse.model_validate(s) for s in rows]

    async def create_session(self, user_id: str, data: SessionCreate) -> SessionResponse:
        item = await self.repo.get_by_id(user_id, data.item_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Learning item not found")
        if data.concept_id:
            concept = await self.repo.get_concept(user_id, data.concept_id)
            if not concept:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Concept not found")
            # Roll session signals into concept when provided
            patch: dict = {}
            if data.can_explain:
                patch["can_explain"] = True
            if data.confidence:
                patch["confidence"] = max(concept.confidence, data.confidence)
            if data.artifact_url:
                patch["artifact_url"] = data.artifact_url
            if patch:
                await self.repo.update_concept(concept, ConceptUpdate(**patch))
                await self._rollup_item_progress(concept.item_id)
        session = await self.repo.create_session(user_id, data)
        return SessionResponse.model_validate(session)

    # --- Concept ↔ knowledge notes ---

    async def list_concept_notes(self, user_id: str, concept_id: str) -> list[ConceptNoteResponse]:
        concept = await self.repo.get_concept(user_id, concept_id)
        if not concept:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Concept not found")
        rows = await self.repo.list_concept_notes(user_id, concept_id)
        return [self._note_response(link, section, chapter, subject) for link, section, chapter, subject in rows]

    async def attach_concept_note(
        self, user_id: str, concept_id: str, data: ConceptNoteCreate
    ) -> ConceptNoteResponse:
        concept = await self.repo.get_concept(user_id, concept_id)
        if not concept:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Concept not found")
        notes_repo = KnowledgeNotesRepository(self.db)

        if data.section_id:
            section = await notes_repo.get_section(user_id, data.section_id)
            if not section:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Note not found")
        else:
            chapter = await self._resolve_chapter(user_id, concept, data, notes_repo)
            section = await notes_repo.create_section(
                user_id,
                chapter.id,
                SectionCreate(title=data.title or concept.title, content=data.content),
            )

        link = await self.repo.find_concept_note(concept_id, section.id)
        if link is None:
            link = await self.repo.create_concept_note(user_id, concept_id, section.id)
        chapter = await notes_repo.get_chapter(user_id, section.chapter_id)
        subject = await notes_repo.get_subject(user_id, chapter.subject_id)
        return self._note_response(link, section, chapter, subject)

    async def detach_concept_note(self, user_id: str, concept_id: str, note_id: str) -> None:
        link = await self.repo.get_concept_note(user_id, note_id)
        if not link or link.concept_id != concept_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Linked note not found")
        await self.repo.delete_concept_note(link)

    async def _resolve_chapter(
        self, user_id: str, concept, data: ConceptNoteCreate, notes_repo: KnowledgeNotesRepository
    ):
        if data.chapter_id:
            chapter = await notes_repo.get_chapter(user_id, data.chapter_id)
            if not chapter:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Chapter not found")
            return chapter

        if data.subject_id:
            subject = await notes_repo.get_subject(user_id, data.subject_id)
            if not subject:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found")
            existing_chapters = list(subject.chapters)
        else:
            subject = await notes_repo.create_subject(
                user_id, SubjectCreate(title=data.subject_title, icon="📚")
            )
            existing_chapters = []

        # Group notes under the phase the concept belongs to, so a subject mirrors the track.
        phase = await self.repo.get_by_id(user_id, concept.item_id)
        chapter_title = data.chapter_title or (phase.title if phase else "Notes")
        for existing in existing_chapters:
            if existing.title == chapter_title:
                return existing
        return await notes_repo.create_chapter(user_id, subject.id, ChapterCreate(title=chapter_title))

    @staticmethod
    def _note_response(link, section, chapter, subject) -> ConceptNoteResponse:
        content = section.content or ""
        return ConceptNoteResponse(
            id=link.id,
            concept_id=link.concept_id,
            section_id=section.id,
            section_title=section.title,
            snippet=content[:200].strip(),
            chapter_id=chapter.id,
            chapter_title=chapter.title,
            subject_id=subject.id,
            subject_title=subject.title,
            route=f"/knowledge/{subject.id}",
            updated_at=section.updated_at,
        )

    async def session_stats(self, user_id: str, weekly_hours_target: int | None = None) -> SessionStats:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        minutes_week = await self.repo.sum_session_minutes(user_id, from_date=week_start, to_date=today)
        minutes_total = await self.repo.sum_session_minutes(user_id)
        total, gated = await self.repo.count_gated_concepts(user_id)
        streak = _study_streak(await self.repo.session_dates(user_id))
        pace = None
        if weekly_hours_target:
            pace = round(minutes_week / 60 - weekly_hours_target, 2)
        return SessionStats(
            minutes_this_week=minutes_week,
            minutes_total=minutes_total,
            concepts_gated=gated,
            concepts_total=total,
            pace_vs_target_hours=pace,
            study_streak_days=streak,
        )
