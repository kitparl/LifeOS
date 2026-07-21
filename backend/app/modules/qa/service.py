from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.qa.models import SUGGESTED_QA_TYPES
from app.modules.qa.repository import QARepository
from app.modules.qa.schemas import QACreate, QAListItem, QAResponse, QAUpdate, QAVersionResponse


class QAService:
    def __init__(self, db: AsyncSession):
        self.repo = QARepository(db)

    def _to_list_item(self, entry) -> QAListItem:
        return QAListItem(
            id=entry.id,
            question=entry.question,
            current_answer=entry.current_answer,
            type=entry.type,
            tags=entry.tags,
            updated_at=entry.updated_at,
        )

    def _to_response(self, entry) -> QAResponse:
        versions = sorted(entry.versions, key=lambda v: v.version_number, reverse=True)
        return QAResponse(
            id=entry.id,
            question=entry.question,
            current_answer=entry.current_answer,
            type=entry.type,
            tags=entry.tags,
            linked_goal_id=entry.linked_goal_id,
            linked_journal_id=entry.linked_journal_id,
            ai_summary=entry.ai_summary,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            versions=[QAVersionResponse.model_validate(v) for v in versions],
        )

    async def list_entries(
        self, user_id: str, search: str | None = None, type_filter: str | None = None
    ) -> list[QAListItem]:
        entries = await self.repo.list_entries(user_id, search=search, type_filter=type_filter)
        return [self._to_list_item(e) for e in entries]

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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type name required")
        await self.repo.ensure_type(user_id, clean)
        return clean

    async def get_entry(self, user_id: str, entry_id: str) -> QAResponse:
        entry = await self.repo.get_by_id(user_id, entry_id)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Q&A entry not found")
        return self._to_response(entry)

    async def create_entry(self, user_id: str, data: QACreate) -> QAResponse:
        entry = await self.repo.create(user_id, data)
        return self._to_response(entry)

    async def update_entry(self, user_id: str, entry_id: str, data: QAUpdate) -> QAResponse:
        entry = await self.repo.get_by_id(user_id, entry_id)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Q&A entry not found")
        updated = await self.repo.update(entry, data)
        return self._to_response(updated)

    async def delete_entry(self, user_id: str, entry_id: str) -> None:
        entry = await self.repo.get_by_id(user_id, entry_id)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Q&A entry not found")
        await self.repo.delete(entry)

    async def list_versions(self, user_id: str, entry_id: str) -> list[QAVersionResponse]:
        entry = await self.repo.get_by_id(user_id, entry_id)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Q&A entry not found")
        versions = sorted(entry.versions, key=lambda v: v.version_number, reverse=True)
        return [QAVersionResponse.model_validate(v) for v in versions]
