from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge_notes.repository import KnowledgeNotesRepository
from app.modules.knowledge_notes.schemas import (
    ChapterCreate,
    ChapterResponse,
    ChapterUpdate,
    SearchHit,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
    SubjectCreate,
    SubjectDetail,
    SubjectListItem,
    SubjectUpdate,
)

ARCHIVE_TTL_DAYS = 7


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")


class KnowledgeNotesService:
    def __init__(self, db: AsyncSession):
        self.repo = KnowledgeNotesRepository(db)

    # ---- Subjects ----
    async def list_subjects(self, user_id: str) -> list[SubjectListItem]:
        await self.repo.purge_expired_archives(user_id, ARCHIVE_TTL_DAYS)
        subjects = await self.repo.list_subjects(user_id)
        items: list[SubjectListItem] = []
        for s in subjects:
            chapters, sections = await self.repo.subject_counts(s.id)
            items.append(
                SubjectListItem(
                    id=s.id,
                    title=s.title,
                    description=s.description,
                    icon=s.icon,
                    order_index=s.order_index,
                    chapter_count=chapters,
                    section_count=sections,
                    updated_at=s.updated_at,
                )
            )
        return items

    async def get_subject(self, user_id: str, subject_id: str) -> SubjectDetail:
        await self.repo.purge_expired_archives(user_id, ARCHIVE_TTL_DAYS)
        subject = await self.repo.get_subject(user_id, subject_id)
        if subject is None:
            raise _not_found("Subject")
        return self._subject_detail(subject)

    def _subject_detail(self, subject) -> SubjectDetail:
        archived: list[SectionResponse] = []
        chapters: list[ChapterResponse] = []
        for chapter in subject.chapters:
            active: list[SectionResponse] = []
            for section in chapter.sections:
                item = SectionResponse.model_validate(section)
                if section.archived_at is None:
                    active.append(item)
                else:
                    archived.append(item)
            chapters.append(
                ChapterResponse(
                    id=chapter.id,
                    subject_id=chapter.subject_id,
                    title=chapter.title,
                    order_index=chapter.order_index,
                    sections=active,
                )
            )
        return SubjectDetail(
            id=subject.id,
            title=subject.title,
            description=subject.description,
            icon=subject.icon,
            order_index=subject.order_index,
            created_at=subject.created_at,
            updated_at=subject.updated_at,
            chapters=chapters,
            archived_sections=archived,
        )

    async def create_subject(self, user_id: str, data: SubjectCreate) -> SubjectDetail:
        subject = await self.repo.create_subject(user_id, data)
        return await self.get_subject(user_id, subject.id)

    async def update_subject(self, user_id: str, subject_id: str, data: SubjectUpdate) -> SubjectDetail:
        subject = await self.repo.get_subject(user_id, subject_id)
        if subject is None:
            raise _not_found("Subject")
        await self.repo.update_subject(subject, data)
        return await self.get_subject(user_id, subject_id)

    async def delete_subject(self, user_id: str, subject_id: str) -> None:
        subject = await self.repo.get_subject(user_id, subject_id)
        if subject is None:
            raise _not_found("Subject")
        await self.repo.delete_subject(subject)

    # ---- Chapters ----
    async def create_chapter(
        self, user_id: str, subject_id: str, data: ChapterCreate
    ) -> ChapterResponse:
        subject = await self.repo.get_subject(user_id, subject_id)
        if subject is None:
            raise _not_found("Subject")
        chapter = await self.repo.create_chapter(user_id, subject_id, data)
        return ChapterResponse.model_validate(chapter)

    async def update_chapter(self, user_id: str, chapter_id: str, data: ChapterUpdate) -> ChapterResponse:
        chapter = await self.repo.get_chapter(user_id, chapter_id)
        if chapter is None:
            raise _not_found("Chapter")
        updated = await self.repo.update_chapter(chapter, data)
        return ChapterResponse.model_validate(updated)

    async def delete_chapter(self, user_id: str, chapter_id: str) -> None:
        chapter = await self.repo.get_chapter(user_id, chapter_id)
        if chapter is None:
            raise _not_found("Chapter")
        await self.repo.delete_chapter(chapter)

    # ---- Sections ----
    async def get_section(self, user_id: str, section_id: str) -> SectionResponse:
        section = await self.repo.get_section(user_id, section_id)
        if section is None:
            raise _not_found("Section")
        return SectionResponse.model_validate(section)

    async def create_section(
        self, user_id: str, chapter_id: str, data: SectionCreate
    ) -> SectionResponse:
        chapter = await self.repo.get_chapter(user_id, chapter_id)
        if chapter is None:
            raise _not_found("Chapter")
        section = await self.repo.create_section(user_id, chapter_id, data)
        return SectionResponse.model_validate(section)

    async def update_section(self, user_id: str, section_id: str, data: SectionUpdate) -> SectionResponse:
        section = await self.repo.get_section(user_id, section_id)
        if section is None:
            raise _not_found("Section")
        # If moving to another chapter, verify ownership of the target.
        if data.chapter_id and data.chapter_id != section.chapter_id:
            target = await self.repo.get_chapter(user_id, data.chapter_id)
            if target is None:
                raise _not_found("Target chapter")
        updated = await self.repo.update_section(section, data)
        return SectionResponse.model_validate(updated)

    async def delete_section(self, user_id: str, section_id: str) -> None:
        section = await self.repo.get_section(user_id, section_id)
        if section is None:
            raise _not_found("Section")
        await self.repo.delete_section(section)

    async def archive_section(self, user_id: str, section_id: str) -> SectionResponse:
        section = await self.repo.get_section(user_id, section_id)
        if section is None:
            raise _not_found("Section")
        updated = await self.repo.archive_section(section)
        return SectionResponse.model_validate(updated)

    async def restore_section(self, user_id: str, section_id: str) -> SectionResponse:
        section = await self.repo.get_section(user_id, section_id)
        if section is None:
            raise _not_found("Section")
        updated = await self.repo.restore_section(section)
        return SectionResponse.model_validate(updated)

    # ---- Search ----
    async def search(self, user_id: str, query: str) -> list[SearchHit]:
        query = (query or "").strip()
        if not query:
            return []
        await self.repo.purge_expired_archives(user_id, ARCHIVE_TTL_DAYS)
        rows = await self.repo.search_sections(user_id, query)
        hits: list[SearchHit] = []
        for section, chapter, subject in rows:
            hits.append(
                SearchHit(
                    section_id=section.id,
                    section_title=section.title,
                    chapter_id=chapter.id,
                    chapter_title=chapter.title,
                    subject_id=subject.id,
                    subject_title=subject.title,
                    snippet=self._snippet(section.content, query),
                )
            )
        return hits

    @staticmethod
    def _snippet(content: str, query: str, radius: int = 60) -> str:
        if not content:
            return ""
        lower = content.lower()
        idx = lower.find(query.lower())
        if idx == -1:
            return content[: radius * 2].strip()
        start = max(0, idx - radius)
        end = min(len(content), idx + len(query) + radius)
        prefix = "…" if start > 0 else ""
        suffix = "…" if end < len(content) else ""
        return f"{prefix}{content[start:end].strip()}{suffix}"
