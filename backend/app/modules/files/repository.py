from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
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

    async def get(
        self,
        user_id: str,
        file_id: str,
        *,
        include_deleted: bool = False,
    ) -> FileRecord | None:
        q = select(FileRecord).where(FileRecord.id == file_id, FileRecord.user_id == user_id)
        if not include_deleted:
            q = q.where(FileRecord.deleted_at.is_(None))
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        file_id: str,
        *,
        include_deleted: bool = False,
    ) -> FileRecord | None:
        q = select(FileRecord).where(FileRecord.id == file_id)
        if not include_deleted:
            q = q.where(FileRecord.deleted_at.is_(None))
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: str,
        *,
        module: str | None = None,
        entity_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[FileRecord], int]:
        filters = [
            FileRecord.user_id == user_id,
            FileRecord.deleted_at.is_(None),
        ]
        if module is not None:
            filters.append(FileRecord.module == module)
        if entity_id is not None:
            filters.append(FileRecord.entity_id == entity_id)

        count_q = select(func.count()).select_from(FileRecord).where(*filters)
        total = int((await self.db.execute(count_q)).scalar_one())

        result = await self.db.execute(
            select(FileRecord)
            .where(*filters)
            .order_by(FileRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def usage_stats(self, user_id: str) -> tuple[int, int]:
        """Return (used_bytes, file_count) including soft-deleted rows (still count toward quota)."""
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(FileRecord.size_bytes), 0),
                func.count(),
            ).where(FileRecord.user_id == user_id)
        )
        used, count = result.one()
        return int(used), int(count)

    async def uploads_in_last_hour(self, user_id: str) -> int:
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        result = await self.db.execute(
            select(func.count()).select_from(FileRecord).where(
                FileRecord.user_id == user_id,
                FileRecord.created_at >= since,
            )
        )
        return int(result.scalar_one())

    async def find_duplicate(
        self,
        user_id: str,
        checksum_sha256: str,
        module: str | None,
        entity_id: str | None,
    ) -> FileRecord | None:
        """Same bytes already stored for this user + module + entity scope."""
        filters = [
            FileRecord.user_id == user_id,
            FileRecord.checksum_sha256 == checksum_sha256,
            FileRecord.deleted_at.is_(None),
            FileRecord.module == module,
        ]
        if entity_id is None:
            filters.append(FileRecord.entity_id.is_(None))
        else:
            filters.append(FileRecord.entity_id == entity_id)
        result = await self.db.execute(select(FileRecord).where(*filters).limit(1))
        return result.scalar_one_or_none()

    async def soft_delete(self, record: FileRecord) -> None:
        record.deleted_at = datetime.now(timezone.utc)
        record.updated_at = record.deleted_at
        await self.db.flush()

    async def hard_delete(self, record: FileRecord) -> None:
        await self.db.delete(record)

    async def delete(self, record: FileRecord) -> None:
        """Legacy name — hard delete for internal callers (e.g. OCR cleanup)."""
        await self.hard_delete(record)

    async def list_purge_candidates(self, older_than: datetime) -> list[FileRecord]:
        result = await self.db.execute(
            select(FileRecord).where(
                FileRecord.deleted_at.is_not(None),
                FileRecord.deleted_at < older_than,
            )
        )
        return list(result.scalars().all())

    async def soft_delete_for_entities(
        self,
        user_id: str,
        module: str,
        entity_ids: list[str],
    ) -> int:
        if not entity_ids:
            return 0
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(FileRecord).where(
                FileRecord.user_id == user_id,
                FileRecord.module == module,
                FileRecord.entity_id.in_(entity_ids),
                FileRecord.deleted_at.is_(None),
            )
        )
        rows = list(result.scalars().all())
        for row in rows:
            row.deleted_at = now
            row.updated_at = now
        if rows:
            await self.db.flush()
        return len(rows)

    async def list_by_storage_backend(self, backend: str) -> list[FileRecord]:
        result = await self.db.execute(
            select(FileRecord).where(FileRecord.storage_backend == backend)
        )
        return list(result.scalars().all())
