from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.knowledge_notes.models import (
    KnowledgeChapter,
    KnowledgeSection,
    KnowledgeSubject,
)
from app.modules.knowledge_notes.schemas import (
    ChapterCreate,
    ChapterUpdate,
    SectionCreate,
    SectionUpdate,
    SubjectCreate,
    SubjectUpdate,
)


class KnowledgeNotesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- Subjects ----
    async def list_subjects(self, user_id: str) -> list[KnowledgeSubject]:
        result = await self.db.execute(
            select(KnowledgeSubject)
            .where(KnowledgeSubject.user_id == user_id)
            .order_by(KnowledgeSubject.order_index, KnowledgeSubject.title)
        )
        return list(result.scalars().all())

    async def get_subject(self, user_id: str, subject_id: str) -> KnowledgeSubject | None:
        result = await self.db.execute(
            select(KnowledgeSubject)
            .where(KnowledgeSubject.id == subject_id, KnowledgeSubject.user_id == user_id)
            .options(
                selectinload(KnowledgeSubject.chapters).selectinload(KnowledgeChapter.sections)
            )
        )
        return result.scalar_one_or_none()

    async def subject_counts(self, subject_id: str) -> tuple[int, int]:
        chapters = await self.db.execute(
            select(func.count(KnowledgeChapter.id)).where(KnowledgeChapter.subject_id == subject_id)
        )
        sections = await self.db.execute(
            select(func.count(KnowledgeSection.id))
            .join(KnowledgeChapter, KnowledgeSection.chapter_id == KnowledgeChapter.id)
            .where(
                KnowledgeChapter.subject_id == subject_id,
                KnowledgeSection.archived_at.is_(None),
            )
        )
        return chapters.scalar_one() or 0, sections.scalar_one() or 0

    async def create_subject(self, user_id: str, data: SubjectCreate) -> KnowledgeSubject:
        max_order = await self.db.execute(
            select(func.max(KnowledgeSubject.order_index)).where(KnowledgeSubject.user_id == user_id)
        )
        subject = KnowledgeSubject(
            user_id=user_id,
            title=data.title,
            description=data.description,
            icon=data.icon,
            order_index=(max_order.scalar_one() or 0) + 1,
        )
        self.db.add(subject)
        await self.db.flush()
        await self.db.refresh(subject)
        return subject

    async def update_subject(self, subject: KnowledgeSubject, data: SubjectUpdate) -> KnowledgeSubject:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(subject, key, value)
        await self.db.flush()
        return await self.get_subject(subject.user_id, subject.id)

    async def delete_subject(self, subject: KnowledgeSubject) -> None:
        await self.db.delete(subject)
        await self.db.flush()

    # ---- Chapters ----
    async def get_chapter(self, user_id: str, chapter_id: str) -> KnowledgeChapter | None:
        result = await self.db.execute(
            select(KnowledgeChapter)
            .where(KnowledgeChapter.id == chapter_id, KnowledgeChapter.user_id == user_id)
            .options(selectinload(KnowledgeChapter.sections))
        )
        return result.scalar_one_or_none()

    async def create_chapter(
        self, user_id: str, subject_id: str, data: ChapterCreate
    ) -> KnowledgeChapter:
        order = data.order_index
        if order is None:
            max_order = await self.db.execute(
                select(func.max(KnowledgeChapter.order_index)).where(
                    KnowledgeChapter.subject_id == subject_id
                )
            )
            order = (max_order.scalar_one() or 0) + 1
        chapter = KnowledgeChapter(
            user_id=user_id, subject_id=subject_id, title=data.title, order_index=order
        )
        self.db.add(chapter)
        await self.db.flush()
        return await self.get_chapter(user_id, chapter.id)

    async def update_chapter(self, chapter: KnowledgeChapter, data: ChapterUpdate) -> KnowledgeChapter:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(chapter, key, value)
        await self.db.flush()
        return await self.get_chapter(chapter.user_id, chapter.id)

    async def delete_chapter(self, chapter: KnowledgeChapter) -> None:
        await self.db.delete(chapter)
        await self.db.flush()

    # ---- Sections ----
    async def get_section(self, user_id: str, section_id: str) -> KnowledgeSection | None:
        result = await self.db.execute(
            select(KnowledgeSection).where(
                KnowledgeSection.id == section_id, KnowledgeSection.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create_section(
        self, user_id: str, chapter_id: str, data: SectionCreate
    ) -> KnowledgeSection:
        order = data.order_index
        if order is None:
            max_order = await self.db.execute(
                select(func.max(KnowledgeSection.order_index)).where(
                    KnowledgeSection.chapter_id == chapter_id,
                    KnowledgeSection.archived_at.is_(None),
                )
            )
            order = (max_order.scalar_one() or 0) + 1
        section = KnowledgeSection(
            user_id=user_id,
            chapter_id=chapter_id,
            title=data.title,
            content=data.content or "",
            order_index=order,
        )
        self.db.add(section)
        await self.db.flush()
        await self.db.refresh(section)
        return section

    async def update_section(self, section: KnowledgeSection, data: SectionUpdate) -> KnowledgeSection:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(section, key, value)
        await self.db.flush()
        await self.db.refresh(section)
        return section

    async def delete_section(self, section: KnowledgeSection) -> None:
        await self.db.delete(section)
        await self.db.flush()

    async def archive_section(self, section: KnowledgeSection) -> KnowledgeSection:
        section.archived_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(section)
        return section

    async def restore_section(self, section: KnowledgeSection) -> KnowledgeSection:
        section.archived_at = None
        await self.db.flush()
        await self.db.refresh(section)
        return section

    async def purge_expired_archives(self, user_id: str, days: int = 7) -> list[str]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(KnowledgeSection).where(
                KnowledgeSection.user_id == user_id,
                KnowledgeSection.archived_at.is_not(None),
                KnowledgeSection.archived_at < cutoff,
            )
        )
        rows = list(result.scalars().all())
        ids = [row.id for row in rows]
        for row in rows:
            await self.db.delete(row)
        if rows:
            await self.db.flush()
        return ids

    # ---- Search ----
    async def search_sections(self, user_id: str, query: str) -> list[tuple]:
        pattern = f"%{query}%"
        result = await self.db.execute(
            select(KnowledgeSection, KnowledgeChapter, KnowledgeSubject)
            .join(KnowledgeChapter, KnowledgeSection.chapter_id == KnowledgeChapter.id)
            .join(KnowledgeSubject, KnowledgeChapter.subject_id == KnowledgeSubject.id)
            .where(
                KnowledgeSection.user_id == user_id,
                KnowledgeSection.archived_at.is_(None),
                or_(
                    KnowledgeSection.title.ilike(pattern),
                    KnowledgeSection.content.ilike(pattern),
                    KnowledgeChapter.title.ilike(pattern),
                    KnowledgeSubject.title.ilike(pattern),
                ),
            )
            .order_by(KnowledgeSection.updated_at.desc())
            .limit(50)
        )
        return list(result.all())
