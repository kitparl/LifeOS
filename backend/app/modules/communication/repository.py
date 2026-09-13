from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.modules.communication.models import (
    SpeakingPractice,
    VocabularyWord,
    WritingAIRun,
    WritingEvaluation,
    WritingPractice,
    WritingRewritePreview,
)
from app.modules.communication.schemas import (
    SpeakingCreate,
    SpeakingUpdate,
    VocabularyCreate,
    VocabularyUpdate,
    WritingCreate,
    WritingUpdate,
)


class CommunicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_vocabulary(
        self,
        user_id: str,
        search: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[VocabularyWord], int]:
        q = select(VocabularyWord).where(VocabularyWord.user_id == user_id)
        if search:
            pattern = f"%{search}%"
            q = q.where(or_(VocabularyWord.word.ilike(pattern), VocabularyWord.meaning.ilike(pattern)))
        q = q.order_by(VocabularyWord.word.asc())
        return await paginate(self.db, q, Pagination(limit=limit, offset=offset))

    async def get_vocabulary(self, user_id: str, word_id: str) -> VocabularyWord | None:
        result = await self.db.execute(
            select(VocabularyWord).where(VocabularyWord.id == word_id, VocabularyWord.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_vocabulary(self, user_id: str, data: VocabularyCreate) -> VocabularyWord:
        word = VocabularyWord(user_id=user_id, **data.model_dump())
        self.db.add(word)
        await self.db.flush()
        await self.db.refresh(word)
        return word

    async def update_vocabulary(self, word: VocabularyWord, data: VocabularyUpdate) -> VocabularyWord:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(word, key, value)
        await self.db.flush()
        await self.db.refresh(word)
        return word

    async def delete_vocabulary(self, word: VocabularyWord) -> None:
        await self.db.delete(word)
        await self.db.flush()

    async def list_writing(
        self,
        user_id: str,
        category: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[WritingPractice], int]:
        q = select(WritingPractice).where(WritingPractice.user_id == user_id)
        if category:
            q = q.where(WritingPractice.category == category)
        q = q.order_by(WritingPractice.updated_at.desc())
        return await paginate(self.db, q, Pagination(limit=limit, offset=offset))

    async def get_writing(self, user_id: str, item_id: str) -> WritingPractice | None:
        result = await self.db.execute(
            select(WritingPractice).where(WritingPractice.id == item_id, WritingPractice.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_writing(self, user_id: str, data: WritingCreate) -> WritingPractice:
        item = WritingPractice(user_id=user_id, **data.model_dump())
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update_writing(self, item: WritingPractice, data: WritingUpdate) -> WritingPractice:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete_writing(self, item: WritingPractice) -> None:
        await self.db.delete(item)
        await self.db.flush()

    async def list_speaking(
        self,
        user_id: str,
        category: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[SpeakingPractice], int]:
        q = select(SpeakingPractice).where(SpeakingPractice.user_id == user_id)
        if category:
            q = q.where(SpeakingPractice.category == category)
        q = q.order_by(SpeakingPractice.updated_at.desc())
        return await paginate(self.db, q, Pagination(limit=limit, offset=offset))

    async def get_speaking(self, user_id: str, item_id: str) -> SpeakingPractice | None:
        result = await self.db.execute(
            select(SpeakingPractice).where(SpeakingPractice.id == item_id, SpeakingPractice.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_speaking(self, user_id: str, data: SpeakingCreate) -> SpeakingPractice:
        item = SpeakingPractice(user_id=user_id, **data.model_dump())
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update_speaking(self, item: SpeakingPractice, data: SpeakingUpdate) -> SpeakingPractice:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete_speaking(self, item: SpeakingPractice) -> None:
        await self.db.delete(item)
        await self.db.flush()

    async def get_evaluation_by_key(
        self, writing_id: str, evaluation_key: str
    ) -> WritingEvaluation | None:
        result = await self.db.execute(
            select(WritingEvaluation).where(
                WritingEvaluation.writing_id == writing_id,
                WritingEvaluation.evaluation_key == evaluation_key,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_evaluation(
        self, user_id: str, writing_id: str
    ) -> WritingEvaluation | None:
        result = await self.db.execute(
            select(WritingEvaluation)
            .where(
                WritingEvaluation.user_id == user_id,
                WritingEvaluation.writing_id == writing_id,
            )
            .order_by(WritingEvaluation.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_evaluation(self, evaluation: WritingEvaluation) -> WritingEvaluation:
        self.db.add(evaluation)
        await self.db.flush()
        await self.db.refresh(evaluation)
        return evaluation

    async def create_ai_run(self, run: WritingAIRun) -> WritingAIRun:
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def update_ai_run(self, run: WritingAIRun) -> WritingAIRun:
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def get_rewrite_by_key(
        self, writing_id: str, rewrite_key: str
    ) -> WritingRewritePreview | None:
        result = await self.db.execute(
            select(WritingRewritePreview).where(
                WritingRewritePreview.writing_id == writing_id,
                WritingRewritePreview.rewrite_key == rewrite_key,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_rewrite(
        self, user_id: str, writing_id: str
    ) -> WritingRewritePreview | None:
        result = await self.db.execute(
            select(WritingRewritePreview)
            .where(
                WritingRewritePreview.user_id == user_id,
                WritingRewritePreview.writing_id == writing_id,
            )
            .order_by(WritingRewritePreview.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_rewrite(self, preview: WritingRewritePreview) -> WritingRewritePreview:
        self.db.add(preview)
        await self.db.flush()
        await self.db.refresh(preview)
        return preview
