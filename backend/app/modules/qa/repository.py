from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    ):
        q = q.where(QAEntry.user_id == user_id)
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
        )

        count_q = select(func.count()).select_from(q.order_by(None).subquery())
        total = (await self.db.execute(count_q)).scalar_one()

        order_col = QAEntry.created_at if sort_by == "created_at" else QAEntry.updated_at
        q = q.order_by(order_col.desc())
        if offset:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all()), int(total)

    async def list_type_names(self, user_id: str) -> list[str]:
        result = await self.db.execute(
            select(QAType.name).where(QAType.user_id == user_id).order_by(QAType.name.asc())
        )
        return list(result.scalars().all())

    async def ensure_type(self, user_id: str, name: str) -> None:
        """Register a type name for reuse (idempotent, case-insensitive)."""
        clean = (name or "").strip()
        if not clean:
            return
        existing = await self.db.execute(
            select(QAType).where(QAType.user_id == user_id)
        )
        for row in existing.scalars().all():
            if row.name.lower() == clean.lower():
                return
        self.db.add(QAType(user_id=user_id, name=clean))
        await self.db.flush()

    async def get_by_id(self, user_id: str, entry_id: str) -> QAEntry | None:
        result = await self.db.execute(
            select(QAEntry)
            .where(QAEntry.id == entry_id, QAEntry.user_id == user_id)
            .options(selectinload(QAEntry.versions))
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: QACreate) -> QAEntry:
        entry = QAEntry(
            user_id=user_id,
            question=data.question,
            current_answer=data.answer,
            type=(data.type or None),
            is_deep_personal=data.is_deep_personal,
            linked_goal_id=data.linked_goal_id,
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
        if data.linked_goal_id is not None:
            entry.linked_goal_id = data.linked_goal_id
        if data.linked_journal_id is not None:
            entry.linked_journal_id = data.linked_journal_id
        if data.answer is not None and data.answer != entry.current_answer:
            entry.current_answer = data.answer
            next_version = max((v.version_number for v in entry.versions), default=0) + 1
            self.db.add(QAVersion(entry_id=entry.id, version_number=next_version, answer=data.answer))
        await self.db.flush()
        await self.db.refresh(entry, ["versions"])
        return entry

    async def delete(self, entry: QAEntry) -> None:
        await self.db.delete(entry)
        await self.db.flush()

    async def list_versions(self, user_id: str, entry_id: str) -> list[QAVersion]:
        entry = await self.get_by_id(user_id, entry_id)
        if entry is None:
            return []
        return sorted(entry.versions, key=lambda v: v.version_number, reverse=True)
