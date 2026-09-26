from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import taxonomy
from app.core.retention import purge_older_than
from app.core.timezone import utc_now
from app.modules.qa.models import QAEntry, QAType, QAVersion
from app.modules.qa.schemas import QACreate, QAUpdate


class QARepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _apply_filters(
        self,
        q,
        user_id: str,
        search: str | None = None,
        type_filter: str | None = None,
        tag: str | None = None,
        deep_personal: bool | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        deleted: bool = False,
    ):
        q = q.where(QAEntry.user_id == user_id)
        if deleted:
            q = q.where(QAEntry.deleted_at.is_not(None))
        else:
            q = q.where(QAEntry.deleted_at.is_(None))
        if search:
            pattern = f"%{search}%"
            q = q.where(or_(QAEntry.question.ilike(pattern), QAEntry.current_answer.ilike(pattern)))
        if type_filter:
            q = q.where(QAEntry.type == type_filter)
        if tag:
            tag_pattern = f'%"{tag.strip()}"%'
            q = q.where(QAEntry.tags_json.ilike(tag_pattern))
        if deep_personal is True:
            q = q.where(QAEntry.is_deep_personal.is_(True))
        elif deep_personal is False:
            q = q.where(QAEntry.is_deep_personal.is_(False))
        if created_from is not None:
            q = q.where(QAEntry.created_at >= created_from)
        if created_to is not None:
            q = q.where(QAEntry.created_at <= created_to)
        return q

    async def list_entries(
        self,
        user_id: str,
        search: str | None = None,
        type_filter: str | None = None,
        tag: str | None = None,
        deep_personal: bool | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        sort_by: str = "updated_at",
        limit: int | None = None,
        offset: int = 0,
        deleted: bool = False,
    ) -> tuple[list[QAEntry], int]:
        q = select(QAEntry)
        q = self._apply_filters(
            q,
            user_id,
            search=search,
            type_filter=type_filter,
            tag=tag,
            deep_personal=deep_personal,
            created_from=created_from,
            created_to=created_to,
            deleted=deleted,
        )

        count_q = select(func.count()).select_from(q.order_by(None).subquery())
        total = (await self.db.execute(count_q)).scalar_one()

        if deleted:
            order_col = QAEntry.deleted_at
        elif sort_by == "created_at":
            order_col = QAEntry.created_at
        else:
            order_col = QAEntry.updated_at
        q = q.order_by(order_col.desc())
        if offset:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all()), int(total)

    async def list_type_names(self, user_id: str) -> list[str]:
        return await taxonomy.list_names(self.db, QAType, user_id)

    async def ensure_type(self, user_id: str, name: str) -> None:
        """Register a name for reuse (idempotent, case-insensitive)."""
        await taxonomy.ensure_name(self.db, QAType, user_id, name)

    async def get_by_id(self, user_id: str, entry_id: str, *, include_deleted: bool = False) -> QAEntry | None:
        q = select(QAEntry).where(QAEntry.id == entry_id, QAEntry.user_id == user_id)
        if not include_deleted:
            q = q.where(QAEntry.deleted_at.is_(None))
        result = await self.db.execute(q.options(selectinload(QAEntry.versions)))
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: QACreate) -> QAEntry:
        entry = QAEntry(
            user_id=user_id,
            question=data.question,
            current_answer=data.answer,
            type=(data.type or None),
            is_deep_personal=data.is_deep_personal,
            linked_journal_id=data.linked_journal_id,
        )
        entry.tags = data.tags
        self.db.add(entry)
        await self.db.flush()
        if data.type:
            await self.ensure_type(user_id, data.type)
        version = QAVersion(entry_id=entry.id, version_number=1, answer=data.answer)
        self.db.add(version)
        await self.db.flush()
        await self.db.refresh(entry, ["versions"])
        return entry

    async def update(self, entry: QAEntry, data: QAUpdate) -> QAEntry:
        if data.question is not None:
            entry.question = data.question
        if data.type is not None:
            entry.type = data.type or None
            if data.type:
                await self.ensure_type(entry.user_id, data.type)
        if data.tags is not None:
            entry.tags = data.tags
        if data.is_deep_personal is not None:
            entry.is_deep_personal = data.is_deep_personal
        if data.linked_journal_id is not None:
            entry.linked_journal_id = data.linked_journal_id
        if data.answer is not None and data.answer != entry.current_answer:
            entry.current_answer = data.answer
            next_version = max((v.version_number for v in entry.versions), default=0) + 1
            self.db.add(QAVersion(entry_id=entry.id, version_number=next_version, answer=data.answer))
        await self.db.flush()
        await self.db.refresh(entry, ["versions"])
        return entry

    async def soft_delete(self, entry: QAEntry) -> None:
        entry.deleted_at = utc_now()
        await self.db.flush()

    async def restore(self, entry: QAEntry) -> None:
        entry.deleted_at = None
        await self.db.flush()

    async def purge_expired(self, days: int) -> int:
        return len(await purge_older_than(self.db, QAEntry, QAEntry.deleted_at, days))

    async def list_versions(self, user_id: str, entry_id: str) -> list[QAVersion]:
        entry = await self.get_by_id(user_id, entry_id)
        if entry is None:
            return []
        return sorted(entry.versions, key=lambda v: v.version_number, reverse=True)
