from datetime import UTC, datetime, timedelta

from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sticky_notes.models import StickyNote
from app.modules.sticky_notes.schemas import StickyNoteCreate, StickyNoteUpdate, normalize_tag

_ORDER = (StickyNote.is_pinned.desc(), StickyNote.order_index.asc())


class StickyNoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_months(self, user_id: str) -> list[tuple[str, int]]:
        result = await self.db.execute(
            select(StickyNote.note_month, func.count(StickyNote.id))
            .where(StickyNote.user_id == user_id, StickyNote.deleted_at.is_(None))
            .group_by(StickyNote.note_month)
            .order_by(StickyNote.note_month.desc())
        )
        return [(month, count) for month, count in result.all()]

    async def list_all(self, user_id: str) -> list[StickyNote]:
        result = await self.db.execute(
            select(StickyNote)
            .where(StickyNote.user_id == user_id, StickyNote.deleted_at.is_(None))
            .order_by(StickyNote.is_pinned.desc(), StickyNote.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_deleted(self, user_id: str) -> list[StickyNote]:
        result = await self.db.execute(
            select(StickyNote)
            .where(StickyNote.user_id == user_id, StickyNote.deleted_at.is_not(None))
            .order_by(StickyNote.deleted_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_month(self, user_id: str, month: str) -> list[StickyNote]:
        result = await self.db.execute(
            select(StickyNote)
            .where(
                StickyNote.user_id == user_id,
                StickyNote.note_month == month,
                StickyNote.deleted_at.is_(None),
            )
            .order_by(*_ORDER)
        )
        return list(result.scalars().all())

    async def list_recent(self, user_id: str, limit: int = 5) -> list[StickyNote]:
        result = await self.db.execute(
            select(StickyNote)
            .where(StickyNote.user_id == user_id, StickyNote.deleted_at.is_(None))
            .order_by(StickyNote.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(self, user_id: str, query: str) -> list[StickyNote]:
        # Text search matches title/content as before. Tag search: every
        # whitespace-separated token (with or without a leading '#') is
        # normalized the same way tags are stored, and a note must carry ALL
        # of them (AND) to match by tag — precise for multi-tag queries.
        # Notes are included if either the text match OR the tag match hits.
        like = f"%{query}%"
        conditions = [StickyNote.title.ilike(like), StickyNote.content.ilike(like)]

        tag_tokens = [normalize_tag(t) for t in query.split()]
        tag_tokens = [t for t in tag_tokens if t]
        if tag_tokens:
            tags_as_text = cast(StickyNote.tags, String)
            conditions.append(and_(*[tags_as_text.ilike(f'%"{t}"%') for t in tag_tokens]))

        result = await self.db.execute(
            select(StickyNote)
            .where(
                StickyNote.user_id == user_id,
                StickyNote.deleted_at.is_(None),
                or_(*conditions),
            )
            .order_by(StickyNote.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, note_id: str, *, include_deleted: bool = False) -> StickyNote | None:
        q = select(StickyNote).where(StickyNote.id == note_id, StickyNote.user_id == user_id)
        if not include_deleted:
            q = q.where(StickyNote.deleted_at.is_(None))
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def min_order_index(self, user_id: str, month: str) -> int:
        result = await self.db.execute(
            select(func.min(StickyNote.order_index)).where(
                StickyNote.user_id == user_id, StickyNote.note_month == month
            )
        )
        return result.scalar_one()

    async def create(self, user_id: str, note_month: str, order_index: int, data: StickyNoteCreate) -> StickyNote:
        note = StickyNote(user_id=user_id, note_month=note_month, order_index=order_index, **data.model_dump())
        self.db.add(note)
        await self.db.flush()
        await self.db.refresh(note)
        return note

    async def update(self, note: StickyNote, data: StickyNoteUpdate) -> StickyNote:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(note, key, value)
        await self.db.flush()
        await self.db.refresh(note)
        return note

    async def soft_delete(self, note: StickyNote) -> None:
        note.deleted_at = datetime.now(UTC)
        await self.db.flush()

    async def restore(self, note: StickyNote) -> None:
        note.deleted_at = None
        await self.db.flush()

    async def purge_expired(self, days: int) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = await self.db.execute(
            select(StickyNote).where(
                StickyNote.deleted_at.is_not(None),
                StickyNote.deleted_at < cutoff,
            )
        )
        rows = list(result.scalars().all())
        for row in rows:
            await self.db.delete(row)
        if rows:
            await self.db.flush()
        return len(rows)
