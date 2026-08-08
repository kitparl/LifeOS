from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.knowledge_notes.models import (
    KnowledgeChapter,
    KnowledgeSection,
    KnowledgeSubject,
)
from app.modules.learning.models import (
    LearningConcept,
    LearningConceptNote,
    LearningItem,
    LearningResource,
    LearningTrack,
    StudySession,
)
from app.modules.learning.schemas import (
    ConceptUpdate,
    LearningCreate,
    LearningUpdate,
    ResourceCreate,
    ResourceUpdate,
    SessionCreate,
    TrackCreate,
)


class LearningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- LearningItem (legacy + phases) ---

    async def list_items(self, user_id: str, item_type: str | None = None) -> list[LearningItem]:
        q = select(LearningItem).where(LearningItem.user_id == user_id)
        if item_type:
            q = q.where(LearningItem.item_type == item_type)
        q = q.order_by(LearningItem.updated_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, item_id: str) -> LearningItem | None:
        result = await self.db.execute(
            select(LearningItem).where(LearningItem.id == item_id, LearningItem.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: LearningCreate) -> LearningItem:
        item = LearningItem(user_id=user_id, **data.model_dump())
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update(self, item: LearningItem, data: LearningUpdate) -> LearningItem:
        for key, value in data.model_dump(exclude_unset=True).items():
            if key == "progress" and value is None:
                continue
            setattr(item, key, value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item: LearningItem) -> None:
        await self.db.delete(item)

    async def get_item_by_slug(self, user_id: str, track_id: str, slug: str) -> LearningItem | None:
        result = await self.db.execute(
            select(LearningItem).where(
                LearningItem.user_id == user_id,
                LearningItem.track_id == track_id,
                LearningItem.slug == slug,
            )
        )
        return result.scalar_one_or_none()

    # --- Tracks ---

    async def list_tracks(self, user_id: str) -> list[LearningTrack]:
        result = await self.db.execute(
            select(LearningTrack)
            .where(LearningTrack.user_id == user_id)
            .order_by(LearningTrack.sort_order, LearningTrack.created_at)
        )
        return list(result.scalars().all())

    async def get_track(self, user_id: str, track_id: str) -> LearningTrack | None:
        result = await self.db.execute(
            select(LearningTrack)
            .where(LearningTrack.id == track_id, LearningTrack.user_id == user_id)
            .options(
                selectinload(LearningTrack.phases).selectinload(LearningItem.concepts).selectinload(
                    LearningConcept.resources
                ),
                selectinload(LearningTrack.phases).selectinload(LearningItem.resources),
            )
        )
        return result.scalar_one_or_none()

    async def get_track_by_slug(self, user_id: str, slug: str) -> LearningTrack | None:
        result = await self.db.execute(
            select(LearningTrack).where(LearningTrack.user_id == user_id, LearningTrack.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_track(self, user_id: str, data: TrackCreate) -> LearningTrack:
        track = LearningTrack(user_id=user_id, **data.model_dump())
        self.db.add(track)
        await self.db.flush()
        await self.db.refresh(track)
        return track

    # --- Concepts ---

    async def list_concepts(
        self, user_id: str, item_id: str | None = None, week: int | None = None
    ) -> list[LearningConcept]:
        q = select(LearningConcept).where(LearningConcept.user_id == user_id)
        if item_id:
            q = q.where(LearningConcept.item_id == item_id)
        if week is not None:
            q = q.where(LearningConcept.week_number == week)
        q = q.order_by(LearningConcept.week_number, LearningConcept.sort_order)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_concept(self, user_id: str, concept_id: str) -> LearningConcept | None:
        result = await self.db.execute(
            select(LearningConcept)
            .where(LearningConcept.id == concept_id, LearningConcept.user_id == user_id)
            .options(
                selectinload(LearningConcept.resources),
                selectinload(LearningConcept.sessions),
            )
        )
        return result.scalar_one_or_none()

    async def get_concept_by_slug(
        self, user_id: str, item_id: str, slug: str
    ) -> LearningConcept | None:
        result = await self.db.execute(
            select(LearningConcept).where(
                LearningConcept.user_id == user_id,
                LearningConcept.item_id == item_id,
                LearningConcept.slug == slug,
            )
        )
        return result.scalar_one_or_none()

    async def update_concept(
        self, concept: LearningConcept, data: ConceptUpdate
    ) -> LearningConcept:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(concept, key, value)
        await self.db.flush()
        await self.db.refresh(concept)
        return concept

    async def count_concepts_for_item(self, item_id: str) -> tuple[int, int]:
        total_result = await self.db.execute(
            select(func.count()).select_from(LearningConcept).where(LearningConcept.item_id == item_id)
        )
        gated_result = await self.db.execute(
            select(func.count())
            .select_from(LearningConcept)
            .where(LearningConcept.item_id == item_id, LearningConcept.can_explain.is_(True))
        )
        return int(total_result.scalar_one()), int(gated_result.scalar_one())

    async def count_concepts_for_track(self, track_id: str) -> tuple[int, int]:
        total_result = await self.db.execute(
            select(func.count())
            .select_from(LearningConcept)
            .join(LearningItem, LearningConcept.item_id == LearningItem.id)
            .where(LearningItem.track_id == track_id)
        )
        gated_result = await self.db.execute(
            select(func.count())
            .select_from(LearningConcept)
            .join(LearningItem, LearningConcept.item_id == LearningItem.id)
            .where(LearningItem.track_id == track_id, LearningConcept.can_explain.is_(True))
        )
        return int(total_result.scalar_one()), int(gated_result.scalar_one())

    # --- Resources ---

    async def list_resources(
        self, user_id: str, concept_id: str | None = None, item_id: str | None = None
    ) -> list[LearningResource]:
        q = select(LearningResource).where(LearningResource.user_id == user_id)
        if concept_id:
            q = q.where(LearningResource.concept_id == concept_id)
        if item_id:
            q = q.where(LearningResource.item_id == item_id)
        q = q.order_by(LearningResource.sort_order)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_resource(self, user_id: str, resource_id: str) -> LearningResource | None:
        result = await self.db.execute(
            select(LearningResource).where(
                LearningResource.id == resource_id, LearningResource.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_resource_by_url(
        self,
        user_id: str,
        url: str,
        concept_id: str | None = None,
        item_id: str | None = None,
    ) -> LearningResource | None:
        q = select(LearningResource).where(
            LearningResource.user_id == user_id, LearningResource.url == url
        )
        if concept_id:
            q = q.where(LearningResource.concept_id == concept_id)
        elif item_id:
            q = q.where(LearningResource.item_id == item_id, LearningResource.concept_id.is_(None))
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def create_resource(self, user_id: str, data: ResourceCreate) -> LearningResource:
        resource = LearningResource(user_id=user_id, **data.model_dump())
        self.db.add(resource)
        await self.db.flush()
        await self.db.refresh(resource)
        return resource

    async def update_resource(
        self, resource: LearningResource, data: ResourceUpdate
    ) -> LearningResource:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(resource, key, value)
        await self.db.flush()
        await self.db.refresh(resource)
        return resource

    # --- Sessions ---

    async def list_sessions(
        self, user_id: str, from_date: date | None = None, to_date: date | None = None
    ) -> list[StudySession]:
        q = select(StudySession).where(StudySession.user_id == user_id)
        if from_date:
            q = q.where(StudySession.session_date >= from_date)
        if to_date:
            q = q.where(StudySession.session_date <= to_date)
        q = q.order_by(StudySession.session_date.desc(), StudySession.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def create_session(self, user_id: str, data: SessionCreate) -> StudySession:
        session = StudySession(user_id=user_id, **data.model_dump())
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def sum_session_minutes(
        self, user_id: str, from_date: date | None = None, to_date: date | None = None,
        track_id: str | None = None,
    ) -> int:
        q = select(func.coalesce(func.sum(StudySession.minutes), 0)).where(
            StudySession.user_id == user_id
        )
        if from_date:
            q = q.where(StudySession.session_date >= from_date)
        if to_date:
            q = q.where(StudySession.session_date <= to_date)
        if track_id:
            q = q.join(LearningItem, StudySession.item_id == LearningItem.id).where(
                LearningItem.track_id == track_id
            )
        result = await self.db.execute(q)
        return int(result.scalar_one())

    async def session_dates(self, user_id: str) -> list[date]:
        result = await self.db.execute(
            select(StudySession.session_date)
            .where(StudySession.user_id == user_id)
            .distinct()
            .order_by(StudySession.session_date.desc())
        )
        return list(result.scalars().all())

    # --- Concept ↔ knowledge notes ---

    async def list_concept_notes(self, user_id: str, concept_id: str) -> list[tuple]:
        result = await self.db.execute(
            select(LearningConceptNote, KnowledgeSection, KnowledgeChapter, KnowledgeSubject)
            .join(KnowledgeSection, LearningConceptNote.section_id == KnowledgeSection.id)
            .join(KnowledgeChapter, KnowledgeSection.chapter_id == KnowledgeChapter.id)
            .join(KnowledgeSubject, KnowledgeChapter.subject_id == KnowledgeSubject.id)
            .where(
                LearningConceptNote.user_id == user_id,
                LearningConceptNote.concept_id == concept_id,
            )
            .order_by(KnowledgeSubject.title, KnowledgeChapter.order_index, KnowledgeSection.order_index)
        )
        return list(result.all())

    async def get_concept_note(self, user_id: str, note_id: str) -> LearningConceptNote | None:
        result = await self.db.execute(
            select(LearningConceptNote).where(
                LearningConceptNote.id == note_id, LearningConceptNote.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def find_concept_note(self, concept_id: str, section_id: str) -> LearningConceptNote | None:
        result = await self.db.execute(
            select(LearningConceptNote).where(
                LearningConceptNote.concept_id == concept_id,
                LearningConceptNote.section_id == section_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_concept_note(
        self, user_id: str, concept_id: str, section_id: str
    ) -> LearningConceptNote:
        link = LearningConceptNote(user_id=user_id, concept_id=concept_id, section_id=section_id)
        self.db.add(link)
        await self.db.flush()
        await self.db.refresh(link)
        return link

    async def delete_concept_note(self, link: LearningConceptNote) -> None:
        await self.db.delete(link)
        await self.db.flush()

    async def count_gated_concepts(self, user_id: str) -> tuple[int, int]:
        total = await self.db.execute(
            select(func.count()).select_from(LearningConcept).where(LearningConcept.user_id == user_id)
        )
        gated = await self.db.execute(
            select(func.count())
            .select_from(LearningConcept)
            .where(LearningConcept.user_id == user_id, LearningConcept.can_explain.is_(True))
        )
        return int(total.scalar_one()), int(gated.scalar_one())
