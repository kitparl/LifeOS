from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.files.models import FileRecord


class FileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, record: FileRecord) -> FileRecord:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def get(self, user_id: str, file_id: str) -> FileRecord | None:
        result = await self.db.execute(
            select(FileRecord).where(FileRecord.id == file_id, FileRecord.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: str, limit: int = 100) -> list[FileRecord]:
        result = await self.db.execute(
            select(FileRecord)
            .where(FileRecord.user_id == user_id)
            .order_by(FileRecord.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete(self, record: FileRecord) -> None:
        await self.db.delete(record)
