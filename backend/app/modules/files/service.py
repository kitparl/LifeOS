import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.modules.files.models import FileRecord
from app.modules.files.repository import FileRepository
from app.modules.files.schemas import FileRecordResponse
from app.modules.files.storage import FileStorage


class FileService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.db = db
        self.repo = FileRepository(db)
        self.settings = settings or get_settings()
        self.storage = FileStorage(self.settings)

    async def upload(
        self,
        user_id: str,
        filename: str,
        content: bytes,
        content_type: str,
        module: str | None = None,
        entity_id: str | None = None,
    ) -> FileRecordResponse:
        if not filename:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Filename required")
        if len(content) > self.settings.max_upload_bytes:
            raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, detail="File too large")

        file_id = str(uuid.uuid4())
        backend, storage_key, url = await self.storage.save(
            user_id, file_id, filename, content, content_type
        )
        record = FileRecord(
            id=file_id,
            user_id=user_id,
            filename=filename,
            content_type=content_type or "application/octet-stream",
            size_bytes=len(content),
            storage_backend=backend,
            storage_key=storage_key,
            url=url,
            module=module,
            entity_id=entity_id,
        )
        saved = await self.repo.create(record)
        return FileRecordResponse.model_validate(saved)

    async def list_files(self, user_id: str) -> list[FileRecordResponse]:
        rows = await self.repo.list_for_user(user_id)
        return [FileRecordResponse.model_validate(r) for r in rows]

    async def get_file(self, user_id: str, file_id: str) -> FileRecordResponse:
        record = await self.repo.get(user_id, file_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        return FileRecordResponse.model_validate(record)

    async def get_local_content(self, user_id: str, file_id: str) -> tuple[FileRecord, bytes]:
        record = await self.repo.get(user_id, file_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        if record.storage_backend != "local":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="File is not stored locally")
        path = self.storage.local_path(record.storage_key)
        if not path.exists():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File content missing")
        return record, path.read_bytes()

    async def delete_file(self, user_id: str, file_id: str) -> None:
        record = await self.repo.get(user_id, file_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")
        await self.storage.delete(record.storage_backend, record.storage_key)
        await self.repo.delete(record)
