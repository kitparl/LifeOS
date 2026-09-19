from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.modules.communication.models import (
    SpeakingPractice,
    WritingAIRun,
    WritingCategory,
    WritingEvaluation,
    WritingPractice,
    WritingRewritePreview,
)
from app.modules.communication.schemas import (
    SpeakingCreate,
    SpeakingUpdate,
    WritingCreate,
    WritingUpdate,
)


class CommunicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def list_category_names(self, user_id: str) -> list[str]:
        result = await self.db.execute(
            select(WritingCategory.name).where(WritingCategory.user_id == user_id).order_by(WritingCategory.name.asc())
        )
        return list(result.scalars().all())

    async def list_used_category_names(self, user_id: str) -> list[str]:
        result = await self.db.execute(
            select(WritingPractice.category).where(WritingPractice.user_id == user_id).distinct()
        )
        return [name for name in result.scalars().all() if name]

    async def ensure_category(self, user_id: str, name: str) -> None:
        clean = (name or "").strip()
        if not clean:
            return
        existing = await self.db.execute(select(WritingCategory).where(WritingCategory.user_id == user_id))
        for row in existing.scalars().all():
            if row.name.lower() == clean.lower():
                return
        self.db.add(WritingCategory(user_id=user_id, name=clean))
        await self.db.flush()

    async def create_writing(self, user_id: str, data: WritingCreate) -> WritingPractice:
        item = WritingPractice(user_id=user_id, **data.model_dump())
        self.db.add(item)
        await self.db.flush()
        if item.category:
            await self.ensure_category(user_id, item.category)
        await self.db.refresh(item)
        return item

    async def update_writing(self, item: WritingPractice, data: WritingUpdate) -> WritingPractice:
        fields = data.model_dump(exclude_unset=True)
        for key, value in fields.items():
            setattr(item, key, value)
        if fields.get("category"):
            await self.ensure_category(item.user_id, fields["category"])
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
