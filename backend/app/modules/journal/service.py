from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.journal.repository import JournalRepository
from app.modules.journal.schemas import JournalCreate, JournalListItem, JournalResponse, JournalUpdate


class JournalService:
    def __init__(self, db: AsyncSession):
        self.repo = JournalRepository(db)

    async def list_entries(
        self, user_id: str, entry_type: str | None = None, search: str | None = None
    ) -> list[JournalListItem]:
        entries = await self.repo.list_entries(user_id, entry_type=entry_type, search=search)
        return [JournalListItem.model_validate(e) for e in entries]

    async def get_entry(self, user_id: str, entry_id: str) -> JournalResponse:
        entry = await self.repo.get_by_id(user_id, entry_id)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
        return JournalResponse.model_validate(entry)

    async def create_entry(self, user_id: str, data: JournalCreate) -> JournalResponse:
        entry = await self.repo.create(user_id, data)
        return JournalResponse.model_validate(entry)

    async def update_entry(self, user_id: str, entry_id: str, data: JournalUpdate) -> JournalResponse:
        entry = await self.repo.get_by_id(user_id, entry_id)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
        updated = await self.repo.update(entry, data)
        return JournalResponse.model_validate(updated)

    async def delete_entry(self, user_id: str, entry_id: str) -> None:
        entry = await self.repo.get_by_id(user_id, entry_id)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
        await self.repo.delete(entry)
