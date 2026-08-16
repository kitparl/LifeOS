from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
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
from app.modules.knowledge_notes.service import KnowledgeNotesService

router = APIRouter(prefix="/knowledge-notes", tags=["knowledge-notes"])


# ---- Search ----
@router.get("/search", response_model=list[SearchHit])
async def search_notes(
    q: str = Query(default=""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).search(user.id, q)


# ---- Subjects ----
@router.get("/subjects", response_model=list[SubjectListItem])
async def list_subjects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).list_subjects(user.id)


@router.post("/subjects", response_model=SubjectDetail, status_code=status.HTTP_201_CREATED)
async def create_subject(
    data: SubjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).create_subject(user.id, data)


@router.get("/subjects/{subject_id}", response_model=SubjectDetail)
async def get_subject(
    subject_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).get_subject(user.id, subject_id)


@router.patch("/subjects/{subject_id}", response_model=SubjectDetail)
async def update_subject(
    subject_id: str,
    data: SubjectUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).update_subject(user.id, subject_id, data)


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await KnowledgeNotesService(db).delete_subject(user.id, subject_id)


# ---- Chapters ----
@router.post(
    "/subjects/{subject_id}/chapters",
    response_model=ChapterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chapter(
    subject_id: str,
    data: ChapterCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).create_chapter(user.id, subject_id, data)


@router.patch("/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    chapter_id: str,
    data: ChapterUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).update_chapter(user.id, chapter_id, data)


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(
    chapter_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await KnowledgeNotesService(db).delete_chapter(user.id, chapter_id)


# ---- Sections ----
@router.post(
    "/chapters/{chapter_id}/sections",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_section(
    chapter_id: str,
    data: SectionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).create_section(user.id, chapter_id, data)


@router.get("/sections/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).get_section(user.id, section_id)


@router.patch("/sections/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: str,
    data: SectionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).update_section(user.id, section_id, data)


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await KnowledgeNotesService(db).delete_section(user.id, section_id)


@router.post("/sections/{section_id}/archive", response_model=SectionResponse)
async def archive_section(
    section_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).archive_section(user.id, section_id)


@router.post("/sections/{section_id}/restore", response_model=SectionResponse)
async def restore_section(
    section_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await KnowledgeNotesService(db).restore_section(user.id, section_id)
