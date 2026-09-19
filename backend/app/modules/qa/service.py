from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.qa.models import SUGGESTED_QA_TYPES
from app.modules.qa.repository import QARepository
from app.modules.qa.schemas import QACreate, QAListItem, QAResponse, QAUpdate, QAVersionResponse
from app.core.exceptions import BadRequestError, get_or_404

QA_PURGE_AFTER_DAYS = 30

class QAService:
    def __init__(self, db: AsyncSession):
        self.repo = QARepository(db)

    def _to_list_item(self, entry, *, include_answer: bool = True) -> QAListItem:
        return QAListItem(
            id=entry.id,
            question=entry.question,
            current_answer=entry.current_answer if include_answer else None,
            type=entry.type,
            tags=entry.tags,
            is_deep_personal=entry.is_deep_personal,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            deleted_at=entry.deleted_at,
        )

    def _to_response(self, entry) -> QAResponse:
        versions = sorted(entry.versions, key=lambda v: v.version_number, reverse=True)
        return QAResponse(
            id=entry.id,
            question=entry.question,
            current_answer=entry.current_answer,
            type=entry.type,
            tags=entry.tags,
            is_deep_personal=entry.is_deep_personal,
            linked_goal_id=entry.linked_goal_id,
            linked_journal_id=entry.linked_journal_id,
            ai_summary=entry.ai_summary,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            versions=[QAVersionResponse.model_validate(v) for v in versions],
        )

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
        include_answer: bool = True,
        deleted: bool = False,
    ) -> tuple[list[QAListItem], int]:
        await self.purge_expired()
        entries, total = await self.repo.list_entries(
            user_id,
            search=search,
            type_filter=type_filter,
            tag=tag,
            deep_personal=deep_personal,
            created_from=created_from,
            created_to=created_to,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
            deleted=deleted,
        )
        return [self._to_list_item(e, include_answer=include_answer) for e in entries], total

    async def list_types(self, user_id: str) -> list[str]:
        """Return the reusable type registry: suggested defaults + user-created,
        de-duplicated (case-insensitive) and alphabetically sorted."""
        stored = await self.repo.list_type_names(user_id)
        seen: dict[str, str] = {}
        for name in [*SUGGESTED_QA_TYPES, *stored]:
            key = name.strip().lower()
            if key and key not in seen:
                seen[key] = name.strip()
        return sorted(seen.values(), key=str.lower)

    async def create_type(self, user_id: str, name: str) -> str:
        clean = name.strip()
        if not clean:
            raise BadRequestError("Type name required")
        await self.repo.ensure_type(user_id, clean)
        return clean

    async def get_entry(self, user_id: str, entry_id: str) -> QAResponse:
        await self.purge_expired()
        entry = get_or_404(await self.repo.get_by_id(user_id, entry_id), "Q&A entry not found")
        return self._to_response(entry)

    async def create_entry(self, user_id: str, data: QACreate) -> QAResponse:
        entry = await self.repo.create(user_id, data)
        return self._to_response(entry)

    async def update_entry(self, user_id: str, entry_id: str, data: QAUpdate) -> QAResponse:
        entry = get_or_404(await self.repo.get_by_id(user_id, entry_id), "Q&A entry not found")
        updated = await self.repo.update(entry, data)
        return self._to_response(updated)

    async def delete_entry(self, user_id: str, entry_id: str) -> None:
        await self.purge_expired()
        entry = get_or_404(await self.repo.get_by_id(user_id, entry_id), "Q&A entry not found")
        await self.repo.soft_delete(entry)

    async def restore_entry(self, user_id: str, entry_id: str) -> QAResponse:
        await self.purge_expired()
        entry = get_or_404(
            await self.repo.get_by_id(user_id, entry_id, include_deleted=True),
            "Q&A entry not found",
        )
        if entry.deleted_at is not None:
            await self.repo.restore(entry)
        return self._to_response(entry)

    async def purge_expired(self, days: int | None = None) -> int:
        return await self.repo.purge_expired(days if days is not None else QA_PURGE_AFTER_DAYS)

    async def list_versions(self, user_id: str, entry_id: str) -> list[QAVersionResponse]:
        entry = get_or_404(await self.repo.get_by_id(user_id, entry_id), "Q&A entry not found")
        versions = sorted(entry.versions, key=lambda v: v.version_number, reverse=True)
        return [QAVersionResponse.model_validate(v) for v in versions]
