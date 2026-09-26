from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin_user, get_current_user, get_optional_user
from app.modules.auth.models import User
from app.modules.files.preview_schemas import PreviewInfoResponse
from app.modules.files.preview_service import DocumentPreviewService
from app.modules.files.schemas import (
    DownloadTokenResponse,
    FileRecordResponse,
    FileUploadResponse,
    FileUsageResponse,
    FileVisibilityUpdate,
    PurgeResponse,
)
from app.modules.files.service import FileService

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/usage", response_model=FileUsageResponse)
async def file_usage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Storage usage. Soft-deleted files still count toward used_bytes until purged."""
    return await FileService(db).get_usage(user.id)


@router.get("/public/{file_id}")
async def get_public_file_content(
    file_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await FileService(db).content_response(file_id=file_id, request=request, public=True)


@router.post("/admin/purge", response_model=PurgeResponse)
async def purge_soft_deleted(
    user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await FileService(db).purge_soft_deleted()


@router.get("", response_model=list[FileRecordResponse])
async def list_files(
    response: Response,
    module: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await FileService(db).list_files(
        user.id,
        module=module,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    module: str | None = Form(default=None),
    entity_id: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FileService(db).upload_file(user.id, file, module, entity_id)


@router.post("/{file_id}/download-token", response_model=DownloadTokenResponse)
async def create_download_token(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FileService(db).create_download_token(user.id, file_id)


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
    request: Request,
    token: str | None = Query(default=None),
    caller: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    return await FileService(db).content_response(
        file_id=file_id,
        request=request,
        user_id=caller.id if caller else None,
        token=token,
    )


@router.get("/{file_id}/preview-info", response_model=PreviewInfoResponse)
async def get_preview_info(
    file_id: str,
    retry: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Metadata + status; idempotently kicks off Office->PDF conversion when needed.

    A "failed" status is stable across plain polling — pass `retry=true`
    (the frontend's Retry button) to attempt the conversion again.
    """
    return await DocumentPreviewService(db).get_preview_info(user.id, file_id, retry=retry)


@router.get("/{file_id}/preview")
async def get_file_preview(
    file_id: str,
    request: Request,
    token: str | None = Query(default=None),
    caller: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Renderable bytes: original for natively-viewable types, converted PDF for Office types."""
    return await DocumentPreviewService(db).stream_preview(
        file_id=file_id,
        request=request,
        user_id=caller.id if caller else None,
        token=token,
    )


@router.get("/{file_id}/download")
async def get_file_download(
    file_id: str,
    request: Request,
    token: str | None = Query(default=None),
    caller: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Always the original bytes, always Content-Disposition: attachment."""
    return await DocumentPreviewService(db).stream_download(
        file_id=file_id,
        request=request,
        user_id=caller.id if caller else None,
        token=token,
    )


@router.patch("/{file_id}", response_model=FileRecordResponse)
async def patch_file(
    file_id: str,
    data: FileVisibilityUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FileService(db).set_visibility(user.id, file_id, data.visibility)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete the file metadata. Bytes remain until admin purge. Soft-deleted rows still count toward quota."""
    await FileService(db).delete_file(user.id, file_id)
