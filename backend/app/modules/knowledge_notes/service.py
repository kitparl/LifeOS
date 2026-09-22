import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.files.repository import FileRepository
from app.modules.knowledge_notes.repository import KnowledgeNotesRepository
from app.core.exceptions import NotFoundError
from app.modules.knowledge_notes.schemas import (
    ChapterCreate,
    ChapterDocument,
    ChapterDocumentsGroup,
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
_INLINE_FILE_RE = re.compile(r"/files/([0-9a-f-]{36})/content", re.I)
_SECTION_FILE_MODULES = ("knowledge_notes", "knowledge_notes_extra")
_DOCUMENT_CONTENT_TYPES = (
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
    "application/rtf",
)


def _file_content_url(file_id: str) -> str:
    return f"/api/v1/files/{file_id}/content"

logger = logging.getLogger(__name__)

def _not_found(what: str) -> NotFoundError:
    return NotFoundError(f"{what} not found")

class KnowledgeNotesService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KnowledgeNotesRepository(db)
        self.files = FileRepository(db)

    async def _purge_expired(self, user_id: str) -> None:
        ids = await self.repo.purge_expired_archives(user_id, ARCHIVE_TTL_DAYS)
        await self._cleanup_section_files(user_id, ids)

    async def _cleanup_section_files(self, user_id: str, section_ids: list[str]) -> None:
        if not section_ids:
            return
        for module in _SECTION_FILE_MODULES:
            await self.files.soft_delete_for_entities(user_id, module, section_ids)

    async def _sync_inline_files(self, user_id: str, section_id: str, content: str) -> None:
        referenced = set(_INLINE_FILE_RE.findall(content or ""))
        rows, _ = await self.files.list_for_user(
            user_id,
            module="knowledge_notes",
            entity_id=section_id,
            limit=500,
        )
        for row in rows:
            if row.id not in referenced:
                await self.files.soft_delete(row)

    # ---- Subjects ----
    async def list_subjects(
        self, user_id: str, limit: int | None = 25, offset: int = 0
    ) -> tuple[list[SubjectListItem], int]:
        await self._purge_expired(user_id)
        subjects, total = await self.repo.list_subjects(user_id, limit=limit, offset=offset)
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
        return items, total

    async def get_subject(self, user_id: str, subject_id: str) -> SubjectDetail:
        await self._purge_expired(user_id)
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
                    closed_at=chapter.closed_at,
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

    async def list_subject_documents(
        self,
        user_id: str,
        subject_id: str,
        chapter_id: str | None = None,
    ) -> list[ChapterDocumentsGroup]:
        subject = await self.repo.get_subject(user_id, subject_id)
        if subject is None:
            raise _not_found("Subject")
        chapters = list(subject.chapters)
        if chapter_id is not None:
            chapters = [chapter for chapter in chapters if chapter.id == chapter_id]
            if not chapters:
                raise _not_found("Chapter")

        section_lookup: dict[str, tuple] = {}
        for chapter in chapters:
            for section in chapter.sections:
                if section.archived_at is None:
                    section_lookup[section.id] = (section, chapter)

        rows = await self.files.list_for_entities(
            user_id,
            list(section_lookup.keys()),
            modules=list(_SECTION_FILE_MODULES),
            content_types=list(_DOCUMENT_CONTENT_TYPES),
        )
        grouped: dict[str, list[ChapterDocument]] = {chapter.id: [] for chapter in chapters}
        for row in rows:
            pair = section_lookup.get(row.entity_id or "")
            if pair is None:
                continue
            section, chapter = pair
            grouped[chapter.id].append(
                ChapterDocument(
                    id=row.id,
                    filename=row.filename,
                    content_type=row.content_type,
                    size_bytes=row.size_bytes,
                    storage_backend=row.storage_backend,
                    url=_file_content_url(row.id),
                    module=row.module,
                    entity_id=row.entity_id,
                    created_at=row.created_at,
                    checksum_sha256=row.checksum_sha256,
                    extension=row.extension,
                    visibility=row.visibility,
                    section_id=section.id,
                    section_title=section.title,
                    chapter_id=chapter.id,
                    chapter_title=chapter.title,
                )
            )

        return [
            ChapterDocumentsGroup(
                chapter_id=chapter.id,
                chapter_title=chapter.title,
                documents=grouped[chapter.id],
            )
            for chapter in chapters
        ]

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
        if data.content is not None:
            await self._sync_inline_files(user_id, section_id, updated.content)
        return SectionResponse.model_validate(updated)

    async def delete_section(self, user_id: str, section_id: str) -> None:
        section = await self.repo.get_section(user_id, section_id)
        if section is None:
            raise _not_found("Section")
        await self.repo.delete_section(section)
        await self._cleanup_section_files(user_id, [section_id])
        try:
            from app.modules.integrations.github.sync_service import GitHubSyncService

            await GitHubSyncService(self.db).delete_section_remote(user_id, section_id)
        except Exception:
            logger.exception("GitHub sync cleanup failed for section=%s", section_id)

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
    async def search(
        self,
        user_id: str,
        query: str,
        subject_id: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[SearchHit], int]:
        query = (query or "").strip()
        if not query:
            return [], 0
        await self._purge_expired(user_id)
        rows, total = await self.repo.search_sections(
            user_id, query, subject_id, limit=limit, offset=offset
        )
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
        return hits, total

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
