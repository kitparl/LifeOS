from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin_user, get_current_user
from app.modules.auth.models import User
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
_optional_bearer = HTTPBearer(auto_error=False)


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
    limit: int = Query(default=100, ge=1, le=500),
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
    creds: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    db: AsyncSession = Depends(get_db),
):
    user_id: str | None = None
    if creds is not None:
        # Bearer path unchanged for existing tests — resolve via get_current_user logic.
        from jose import JWTError

        from app.core.security import decode_token, verify_token_type
        from sqlalchemy import select

        try:
            payload = decode_token(creds.credentials)
            user_id = verify_token_type(payload, "access")
        except JWTError:
            from fastapi import HTTPException

            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        user_id = user.id

    return await FileService(db).content_response(
        file_id=file_id,
        request=request,
        user_id=user_id,
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
