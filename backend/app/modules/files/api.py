from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.files.schemas import FileRecordResponse, FileUploadResponse
from app.modules.files.service import FileService

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=list[FileRecordResponse])
async def list_files(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FileService(db).list_files(user.id)


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    module: str | None = Form(default=None),
    entity_id: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    return await FileService(db).upload(
        user.id,
        file.filename or "upload",
        content,
        file.content_type or "application/octet-stream",
        module,
        entity_id,
    )


@router.get("/{file_id}", response_model=FileRecordResponse)
async def get_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FileService(db).get_file(user.id, file_id)


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record, content = await FileService(db).get_local_content(user.id, file_id)
    return Response(content=content, media_type=record.content_type)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await FileService(db).delete_file(user.id, file_id)
