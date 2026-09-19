from __future__ import annotations

import asyncio
import logging
import tempfile
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError, get_or_404
from app.modules.files.backends import resolve_backend
from app.modules.files.download_tokens import verify_download_token
from app.modules.files.models import FileRecord
from app.modules.files.preview.office_converter import (
    ConversionError,
    ConversionTimeoutError,
    convert_to_pdf,
)
from app.modules.files.preview.ooxml import is_ooxml_mime, verify_ooxml_structure
from app.modules.files.preview.providers import CONVERTER_VERSION, detect_preview_type
from app.modules.files.preview_models import DocumentPreview
from app.modules.files.preview_schemas import PreviewInfoResponse
from app.modules.files.repository import FileRepository
from app.modules.files.service import FileService
from fastapi import Request, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024

# Per-cache-key locks preventing duplicate conversions of the same document
# within one worker process. In-process only — see README "known limitations":
# with multiple uvicorn workers, two workers could each convert a document
# once concurrently, which is wasteful but not corrupting (cache writes are
# atomic via temp-file + os.replace, same as LocalStorageBackend).
_conversion_locks: dict[str, asyncio.Lock] = {}
_background_tasks: set[asyncio.Task] = set()


def _get_lock(cache_key: str) -> asyncio.Lock:
    lock = _conversion_locks.get(cache_key)
    if lock is None:
        lock = asyncio.Lock()
        _conversion_locks[cache_key] = lock
    return lock


def _cache_key_for(record: FileRecord) -> str:
    checksum = record.checksum_sha256 or "no-checksum"
    return f"{checksum}-{CONVERTER_VERSION}"


class DocumentPreviewService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.repo = FileRepository(db)
        self.files = FileService(db, self.settings)
        # Captured so the detached background conversion task opens its own
        # session against the SAME engine as this request (not a fresh
        # `app.core.database.async_session_factory`, which in tests points
        # at a different database than the per-test override).
        self._session_factory = async_sessionmaker(db.bind, class_=AsyncSession, expire_on_commit=False)

    def _cache_path(self, file_id: str, cache_key: str) -> Path:
        return Path(self.settings.preview_cache_dir).resolve() / file_id / f"{cache_key}.pdf"

    async def get_preview_info(self, user_id: str, file_id: str, *, retry: bool = False) -> PreviewInfoResponse:
        record = get_or_404(await self.repo.get(user_id, file_id), "File not found")
        preview_type = detect_preview_type(record.content_type)
        download_url = f"/api/v1/files/{file_id}/download"

        if preview_type == "unsupported":
            return PreviewInfoResponse(
                document_id=file_id,
                file_name=record.filename,
                original_mime_type=record.content_type,
                preview_type="unsupported",
                status="ready",
                preview_url=None,
                download_url=download_url,
            )

        is_office_conversion = preview_type == "pdf" and record.content_type != "application/pdf"
        if not is_office_conversion:
            return PreviewInfoResponse(
                document_id=file_id,
                file_name=record.filename,
                original_mime_type=record.content_type,
                preview_type=preview_type,
                status="ready",
                preview_url=f"/api/v1/files/{file_id}/preview",
                download_url=download_url,
            )

        if record.size_bytes > self.settings.preview_max_file_bytes:
            return PreviewInfoResponse(
                document_id=file_id,
                file_name=record.filename,
                original_mime_type=record.content_type,
                preview_type="unsupported",
                status="ready",
                preview_url=None,
                download_url=download_url,
                error="File too large to preview",
            )

        row = await self._ensure_conversion_scheduled(record, retry=retry)
        return PreviewInfoResponse(
            document_id=file_id,
            file_name=record.filename,
            original_mime_type=record.content_type,
            preview_type="pdf",
            status=row.status,
            preview_url=f"/api/v1/files/{file_id}/preview" if row.status == "ready" else None,
            download_url=download_url,
            error=row.error,
        )

    async def _ensure_conversion_scheduled(self, record: FileRecord, *, retry: bool = False) -> DocumentPreview:
        """Idempotent: returns the current (possibly just-created) status row.

        Only the request that wins the insert/reset schedules a conversion —
        concurrent callers for the same file just observe "processing". A
        "failed" row is a STABLE terminal state on plain polling — it is only
        re-attempted when the file changed (cache_key differs) or the caller
        explicitly asks to retry (`retry=True`). Without this, every routine
        status poll after a failure would silently reschedule and flip the
        status back to "processing" before the caller could ever observe
        "failed".
        """
        cache_key = _cache_key_for(record)
        row = await self.db.get(DocumentPreview, record.id)

        if row is not None and row.cache_key == cache_key and (row.status != "failed" or not retry):
            return row

        if row is not None:
            # Stale cache (re-uploaded) or an explicit retry — (re)convert in place.
            row.cache_key = cache_key
            row.status = "processing"
            row.error = None
            row.cache_path = None
            await self.db.flush()
            self._schedule_conversion(record.id, cache_key)
            return row

        row = DocumentPreview(file_id=record.id, cache_key=cache_key, preview_type="pdf", status="processing")
        self.db.add(row)
        try:
            await self.db.flush()
        except IntegrityError:
            # Lost a race with a concurrent request creating the same row first.
            await self.db.rollback()
            return get_or_404(await self.db.get(DocumentPreview, record.id), "Preview state missing")
        self._schedule_conversion(record.id, cache_key)
        return row

    def _schedule_conversion(self, file_id: str, cache_key: str) -> None:
        lock = _get_lock(cache_key)
        if lock.locked():
            return  # Already converting in this worker process.
        task = asyncio.create_task(self._convert(file_id, cache_key, lock))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

    async def _convert(self, file_id: str, cache_key: str, lock: asyncio.Lock) -> None:
        async with lock, self._session_factory() as db:
            try:
                record = await FileRepository(db).get_by_id(file_id)
                if record is None or _cache_key_for(record) != cache_key:
                    return  # File deleted or changed since scheduling.

                tmp_input: Path | None = None
                try:
                    suffix = f".{record.extension.lstrip('.')}" if record.extension else ""
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                        tmp_input = Path(tmp.name)
                        backend = resolve_backend(record.storage_backend, self.settings)
                        stream = await backend.open(record.storage_key)
                        async for chunk in stream:
                            tmp.write(chunk)

                    if is_ooxml_mime(record.content_type) and not verify_ooxml_structure(tmp_input):
                        await self._mark_failed(db, file_id, "File does not match its declared type")
                        return

                    pdf_bytes = await convert_to_pdf(
                        tmp_input, timeout_seconds=self.settings.conversion_timeout_seconds
                    )
                finally:
                    if tmp_input is not None:
                        tmp_input.unlink(missing_ok=True)

                cache_path = self._cache_path(file_id, cache_key)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                tmp_out = cache_path.with_name(f".tmp_{uuid.uuid4().hex}.pdf")
                tmp_out.write_bytes(pdf_bytes)
                tmp_out.replace(cache_path)

                row = await db.get(DocumentPreview, file_id)
                if row is not None:
                    row.status = "ready"
                    row.cache_path = str(cache_path)
                    row.error = None
                    await db.commit()
            except (ConversionError, ConversionTimeoutError) as exc:
                await self._mark_failed(db, file_id, str(exc))
            except Exception:
                logger.exception("Unexpected error converting file_id=%s", file_id)
                await self._mark_failed(db, file_id, "Conversion failed")

    async def _mark_failed(self, db: AsyncSession, file_id: str, error: str) -> None:
        row = await db.get(DocumentPreview, file_id)
        if row is not None:
            row.status = "failed"
            row.error = error
            await db.commit()

    async def stream_preview(
        self,
        *,
        file_id: str,
        request: Request,
        user_id: str | None = None,
        token: str | None = None,
    ) -> Response:
        record = await self._resolve_record(file_id, user_id=user_id, token=token)
        preview_type = detect_preview_type(record.content_type)
        if preview_type == "unsupported":
            raise NotFoundError("Preview not available for this file")

        if preview_type != "pdf" or record.content_type == "application/pdf":
            return await self.files.content_response(
                file_id=file_id,
                request=request,
                user_id=user_id,
                token=token,
                force_disposition="inline",
            )

        row = await self.db.get(DocumentPreview, file_id)
        if row is None or row.status != "ready" or not row.cache_path:
            raise ConflictError("Preview is still processing")
        return await self._stream_local_pdf(Path(row.cache_path), request)

    async def stream_download(
        self,
        *,
        file_id: str,
        request: Request,
        user_id: str | None = None,
        token: str | None = None,
    ) -> Response:
        return await self.files.content_response(
            file_id=file_id,
            request=request,
            user_id=user_id,
            token=token,
            force_disposition="attachment",
        )

    async def _resolve_record(self, file_id: str, *, user_id: str | None, token: str | None) -> FileRecord:
        if token:
            try:
                token_user = verify_download_token(token, file_id, self.settings)
            except ValueError as exc:
                raise UnauthorizedError("Invalid download token") from exc
            return get_or_404(await self.repo.get(token_user, file_id), "File not found")
        if user_id:
            return get_or_404(await self.repo.get(user_id, file_id), "File not found")
        raise UnauthorizedError("Not authenticated")

    async def _stream_local_pdf(self, path: Path, request: Request) -> Response:
        if not path.is_file():
            raise NotFoundError("Preview not available")
        size = path.stat().st_size
        headers = {
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": "inline",
            "Accept-Ranges": "bytes",
            "Cache-Control": "private, max-age=300",
        }
        range_header = request.headers.get("range")

        if range_header and range_header.startswith("bytes="):
            start, end = FileService._parse_range(range_header, size)
            length = end - start + 1
            headers["Content-Range"] = f"bytes {start}-{end}/{size}"
            headers["Content-Length"] = str(length)

            async def ranged() -> AsyncIterator[bytes]:
                with path.open("rb") as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk = f.read(min(CHUNK_SIZE, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            return StreamingResponse(
                ranged(),
                status_code=status.HTTP_206_PARTIAL_CONTENT,
                media_type="application/pdf",
                headers=headers,
            )

        headers["Content-Length"] = str(size)

        async def full() -> AsyncIterator[bytes]:
            with path.open("rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    yield chunk

        return StreamingResponse(full(), media_type="application/pdf", headers=headers)
