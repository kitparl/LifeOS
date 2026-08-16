from __future__ import annotations

import hashlib
import logging
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from fastapi import HTTPException, Request, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.modules.files.backends import get_storage_backend, resolve_backend
from app.modules.files.backends.base import StorageBackend
from app.modules.files.download_tokens import mint_download_token, verify_download_token
from app.modules.files.keys import build_storage_key
from app.modules.files.models import FileRecord
from app.modules.files.repository import FileRepository
from app.modules.files.schemas import (
    DownloadTokenResponse,
    FileRecordResponse,
    FileUsageResponse,
    PurgeResponse,
)
from app.modules.files.validation import (
    INLINE_SAFE_TYPES,
    NEVER_INLINE_TYPES,
    extension_for_mime,
    sniff_content_type,
    validate_module,
)

logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024


def _derived_url(file_id: str) -> str:
    return f"/api/v1/files/{file_id}/content"


def _to_response(record: FileRecord) -> FileRecordResponse:
    data = FileRecordResponse.model_validate(record)
    # Derive URL at read time (D2); keep response field for frontend.
    return data.model_copy(update={"url": _derived_url(record.id)})


class FileService:
    def __init__(
        self,
        db: AsyncSession,
        settings: Settings | None = None,
        storage: StorageBackend | None = None,
    ):
        self.db = db
        self.repo = FileRepository(db)
        self.settings = settings or get_settings()
        self.storage = storage or get_storage_backend()

    def _backend_for(self, record: FileRecord) -> StorageBackend:
        return resolve_backend(record.storage_backend, self.settings)

    async def upload(
        self,
        user_id: str,
        filename: str,
        content: bytes,
        content_type: str,
        module: str | None = None,
        entity_id: str | None = None,
    ) -> FileRecordResponse:
        """Bytes-based upload kept for OCR / Telegram callers."""

        async def _gen() -> AsyncIterator[bytes]:
            yield content

        return await self.upload_stream(
            user_id,
            filename,
            _gen(),
            content_type,
            module,
            entity_id,
        )

    async def upload_stream(
        self,
        user_id: str,
        filename: str,
        stream: AsyncIterator[bytes],
        content_type: str,
        module: str | None = None,
        entity_id: str | None = None,
    ) -> FileRecordResponse:
        if not filename:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Filename required")

        module = validate_module(module)
        await self._enforce_rate_limit(user_id)
        await self._enforce_quota(user_id, additional=0)

        # Read first chunk: size check before type validation (existing 413 test).
        first = b""
        async for chunk in stream:
            first = chunk
            break
        if len(first) > self.settings.max_upload_bytes:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, detail="File too large")

        sniffed = sniff_content_type(first[:8192], filename, self.settings)
        ext = extension_for_mime(sniffed)
        file_id = str(uuid.uuid4())
        storage_key = build_storage_key(
            module=module,
            entity_id=entity_id,
            file_id=file_id,
            extension=ext,
        )
        storage = get_storage_backend()
        backend_name = (self.settings.storage_backend or "local").strip().lower()
        if backend_name not in ("local", "s3"):
            backend_name = "local"

        max_bytes = self.settings.max_upload_bytes
        hasher = hashlib.sha256()
        total = 0
        rest_iter = stream

        async def limited() -> AsyncIterator[bytes]:
            nonlocal total
            if first:
                total += len(first)
                if total > max_bytes:
                    raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, detail="File too large")
                hasher.update(first)
                yield first
            async for chunk in rest_iter:
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, detail="File too large")
                hasher.update(chunk)
                yield chunk

        try:
            stored = await storage.save(storage_key, limited(), sniffed)
        except HTTPException:
            try:
                await storage.delete(storage_key)
            except Exception:
                pass
            raise

        size_bytes = stored.size_bytes
        checksum = stored.checksum_sha256 or hasher.hexdigest()

        existing = await self.repo.find_duplicate(user_id, checksum, module, entity_id)
        if existing:
            try:
                await storage.delete(storage_key)
            except Exception:
                logger.exception("Failed to clean up duplicate upload: %s", storage_key)
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="This file has already been uploaded",
            )

        await self._enforce_quota(user_id, additional=size_bytes)

        url = _derived_url(file_id)
        record = FileRecord(
            id=file_id,
            user_id=user_id,
            filename=filename,
            content_type=sniffed,
            size_bytes=size_bytes,
            storage_backend=backend_name,
            storage_key=storage_key,
            url=url,
            module=module,
            entity_id=entity_id,
            checksum_sha256=checksum,
            extension=ext.lstrip(".") if ext else None,
            visibility="private",
            updated_at=datetime.now(timezone.utc),
        )
        try:
            saved = await self.repo.create(record)
        except Exception:
            try:
                await storage.delete(storage_key)
            except Exception:
                logger.exception("Failed to clean up storage object after DB error: %s", storage_key)
            raise
        return _to_response(saved)

    async def upload_file(
        self,
        user_id: str,
        upload: UploadFile,
        module: str | None = None,
        entity_id: str | None = None,
    ) -> FileRecordResponse:
        async def _stream() -> AsyncIterator[bytes]:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk

        return await self.upload_stream(
            user_id,
            upload.filename or "upload",
            _stream(),
            upload.content_type or "application/octet-stream",
            module,
            entity_id,
        )

    async def _enforce_rate_limit(self, user_id: str) -> None:
        count = await self.repo.uploads_in_last_hour(user_id)
        if count >= self.settings.uploads_per_hour:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Upload rate limit exceeded",
            )

    async def _enforce_quota(self, user_id: str, *, additional: int) -> None:
        used, _ = await self.repo.usage_stats(user_id)
        if used + additional > self.settings.user_storage_quota_bytes:
            raise HTTPException(
                status.HTTP_413_CONTENT_TOO_LARGE,
                detail="User storage quota exceeded",
            )

    async def list_files(
        self,
        user_id: str,
        *,
        module: str | None = None,
        entity_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[FileRecordResponse], int]:
        rows, total = await self.repo.list_for_user(
            user_id,
            module=module,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )
        return [_to_response(r) for r in rows], total

    async def get_file(self, user_id: str, file_id: str) -> FileRecordResponse:
        record = await self.repo.get(user_id, file_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        return _to_response(record)

    async def get_usage(self, user_id: str) -> FileUsageResponse:
        used, count = await self.repo.usage_stats(user_id)
        return FileUsageResponse(
            used_bytes=used,
            quota_bytes=self.settings.user_storage_quota_bytes,
            file_count=count,
        )

    async def create_download_token(self, user_id: str, file_id: str) -> DownloadTokenResponse:
        record = await self.repo.get(user_id, file_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        token, expires_at = mint_download_token(file_id, user_id, self.settings)
        return DownloadTokenResponse(token=token, expires_at=expires_at)

    async def set_visibility(self, user_id: str, file_id: str, visibility: str) -> FileRecordResponse:
        record = await self.repo.get(user_id, file_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        old = record.visibility
        record.visibility = visibility
        record.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(record)
        logger.info(
            "file_visibility_changed file_id=%s user_id=%s from=%s to=%s",
            file_id,
            user_id,
            old,
            visibility,
        )
        return _to_response(record)

    async def delete_file(self, user_id: str, file_id: str) -> None:
        """Soft-delete: set deleted_at; bytes remain until purge. Soft-deleted rows still count toward quota."""
        record = await self.repo.get(user_id, file_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        await self.repo.soft_delete(record)

    async def hard_delete_file(self, user_id: str, file_id: str) -> None:
        record = await self.repo.get(user_id, file_id, include_deleted=True)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        backend = self._backend_for(record)
        await backend.delete(record.storage_key)
        await self.repo.hard_delete(record)

    async def purge_soft_deleted(self, *, older_than_days: int | None = None) -> PurgeResponse:
        days = older_than_days if older_than_days is not None else self.settings.file_purge_after_days
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        candidates = await self.repo.list_purge_candidates(cutoff)
        purged = 0
        for record in candidates:
            backend = self._backend_for(record)
            try:
                await backend.delete(record.storage_key)
            except Exception:
                logger.exception("Failed to delete bytes for %s", record.id)
            await self.repo.hard_delete(record)
            purged += 1
        return PurgeResponse(purged=purged)

    async def content_response(
        self,
        *,
        file_id: str,
        request: Request,
        user_id: str | None = None,
        token: str | None = None,
        public: bool = False,
    ) -> Response:
        if public:
            record = await self.repo.get_by_id(file_id)
            if not record or record.visibility != "public":
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        elif token:
            try:
                token_user = verify_download_token(token, file_id, self.settings)
            except ValueError:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid download token")
            record = await self.repo.get(token_user, file_id)
            if not record:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        elif user_id:
            record = await self.repo.get(user_id, file_id)
            if not record:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        else:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        etag = f'"{record.checksum_sha256}"' if record.checksum_sha256 else None
        if etag and request.headers.get("if-none-match") == etag:
            return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})

        backend = self._backend_for(record)
        content_type = record.content_type
        disposition = self._content_disposition(record)

        range_header = request.headers.get("range")
        size = record.size_bytes

        headers = {
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": disposition,
            "Accept-Ranges": "bytes",
        }
        if etag:
            headers["ETag"] = etag
        if public:
            headers["Cache-Control"] = "public, max-age=3600"
        else:
            headers["Cache-Control"] = "private, max-age=300"

        if range_header and range_header.startswith("bytes="):
            start, end = self._parse_range(range_header, size)
            length = end - start + 1
            headers["Content-Range"] = f"bytes {start}-{end}/{size}"
            headers["Content-Length"] = str(length)

            async def ranged() -> AsyncIterator[bytes]:
                stream = await backend.open(record.storage_key)
                offset = 0
                remaining = length
                async for chunk in stream:
                    if offset + len(chunk) <= start:
                        offset += len(chunk)
                        continue
                    if offset < start:
                        chunk = chunk[start - offset :]
                        offset = start
                    if remaining <= 0:
                        break
                    if len(chunk) > remaining:
                        yield chunk[:remaining]
                        break
                    yield chunk
                    remaining -= len(chunk)
                    offset += len(chunk)

            return StreamingResponse(
                ranged(),
                status_code=status.HTTP_206_PARTIAL_CONTENT,
                media_type=content_type,
                headers=headers,
            )

        headers["Content-Length"] = str(size)

        async def full() -> AsyncIterator[bytes]:
            stream = await backend.open(record.storage_key)
            async for chunk in stream:
                yield chunk

        return StreamingResponse(full(), media_type=content_type, headers=headers)

    def _content_disposition(self, record: FileRecord) -> str:
        filename = record.filename.replace('"', "").replace("\\", "")
        encoded = quote(filename, safe="")
        ascii_name = "".join(ch if 32 <= ord(ch) < 127 else "_" for ch in filename).strip("._") or "file"
        if record.content_type in NEVER_INLINE_TYPES:
            kind = "attachment"
        elif record.content_type in INLINE_SAFE_TYPES:
            kind = "inline"
        else:
            kind = "attachment"
        return f"{kind}; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}"

    @staticmethod
    def _parse_range(header: str, size: int) -> tuple[int, int]:
        try:
            unit, _, rng = header.partition("=")
            if unit.strip() != "bytes":
                raise ValueError
            start_s, _, end_s = rng.partition("-")
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else size - 1
            if start < 0 or end >= size or start > end:
                raise ValueError
            return start, end
        except ValueError:
            raise HTTPException(
                status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                detail="Invalid Range",
                headers={"Content-Range": f"bytes */{size}"},
            )
