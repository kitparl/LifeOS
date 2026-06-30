from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.communication.repository import CommunicationRepository
from app.modules.communication.schemas import (
    SpeakingCreate,
    SpeakingResponse,
    SpeakingUpdate,
    VocabularyCreate,
    VocabularyResponse,
    VocabularyUpdate,
    WritingCreate,
    WritingResponse,
    WritingUpdate,
)


class CommunicationService:
    def __init__(self, db: AsyncSession):
        self.repo = CommunicationRepository(db)

    async def list_vocabulary(self, user_id: str, search: str | None = None) -> list[VocabularyResponse]:
        words = await self.repo.list_vocabulary(user_id, search=search)
        return [VocabularyResponse.model_validate(w) for w in words]

    async def get_vocabulary(self, user_id: str, word_id: str) -> VocabularyResponse:
        word = await self.repo.get_vocabulary(user_id, word_id)
        if word is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
        return VocabularyResponse.model_validate(word)

    async def create_vocabulary(self, user_id: str, data: VocabularyCreate) -> VocabularyResponse:
        word = await self.repo.create_vocabulary(user_id, data)
        return VocabularyResponse.model_validate(word)

    async def update_vocabulary(self, user_id: str, word_id: str, data: VocabularyUpdate) -> VocabularyResponse:
        word = await self.repo.get_vocabulary(user_id, word_id)
        if word is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
        updated = await self.repo.update_vocabulary(word, data)
        return VocabularyResponse.model_validate(updated)

    async def delete_vocabulary(self, user_id: str, word_id: str) -> None:
        word = await self.repo.get_vocabulary(user_id, word_id)
        if word is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
        await self.repo.delete_vocabulary(word)

    async def list_writing(self, user_id: str, category: str | None = None) -> list[WritingResponse]:
        items = await self.repo.list_writing(user_id, category=category)
        return [WritingResponse.model_validate(i) for i in items]

    async def get_writing(self, user_id: str, item_id: str) -> WritingResponse:
        item = await self.repo.get_writing(user_id, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing not found")
        return WritingResponse.model_validate(item)

    async def create_writing(self, user_id: str, data: WritingCreate) -> WritingResponse:
        item = await self.repo.create_writing(user_id, data)
        return WritingResponse.model_validate(item)

    async def update_writing(self, user_id: str, item_id: str, data: WritingUpdate) -> WritingResponse:
        item = await self.repo.get_writing(user_id, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing not found")
        updated = await self.repo.update_writing(item, data)
        return WritingResponse.model_validate(updated)

    async def delete_writing(self, user_id: str, item_id: str) -> None:
        item = await self.repo.get_writing(user_id, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing not found")
        await self.repo.delete_writing(item)

    async def list_speaking(self, user_id: str, category: str | None = None) -> list[SpeakingResponse]:
        items = await self.repo.list_speaking(user_id, category=category)
        return [SpeakingResponse.model_validate(i) for i in items]

    async def get_speaking(self, user_id: str, item_id: str) -> SpeakingResponse:
        item = await self.repo.get_speaking(user_id, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaking practice not found")
        return SpeakingResponse.model_validate(item)

    async def create_speaking(self, user_id: str, data: SpeakingCreate) -> SpeakingResponse:
        item = await self.repo.create_speaking(user_id, data)
        return SpeakingResponse.model_validate(item)

    async def update_speaking(self, user_id: str, item_id: str, data: SpeakingUpdate) -> SpeakingResponse:
        item = await self.repo.get_speaking(user_id, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaking practice not found")
        updated = await self.repo.update_speaking(item, data)
        return SpeakingResponse.model_validate(updated)

    async def delete_speaking(self, user_id: str, item_id: str) -> None:
        item = await self.repo.get_speaking(user_id, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaking practice not found")
        await self.repo.delete_speaking(item)
