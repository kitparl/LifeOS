import json
import math
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import (
    AIUseCaseModelSelection,
    AIUseCaseModelSelectionHistory,
    ContentEmbedding,
)


class AiRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def clear_user_index(self, user_id: str) -> None:
        await self.db.execute(delete(ContentEmbedding).where(ContentEmbedding.user_id == user_id))

    async def upsert_chunk(self, chunk: ContentEmbedding) -> ContentEmbedding:
        result = await self.db.execute(
            select(ContentEmbedding).where(
                ContentEmbedding.user_id == chunk.user_id,
                ContentEmbedding.source_type == chunk.source_type,
                ContentEmbedding.source_id == chunk.source_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.title = chunk.title
            existing.content = chunk.content
            existing.route = chunk.route
            existing.embedding_json = chunk.embedding_json
            await self.db.flush()
            return existing
        self.db.add(chunk)
        await self.db.flush()
        return chunk

    async def list_for_user(self, user_id: str) -> list[ContentEmbedding]:
        result = await self.db.execute(
            select(ContentEmbedding).where(ContentEmbedding.user_id == user_id)
        )
        return list(result.scalars().all())

    async def count_for_user(self, user_id: str) -> tuple[int, int]:
        rows = await self.list_for_user(user_id)
        embedded = sum(1 for r in rows if r.embedding_json)
        return len(rows), embedded

    async def get_selection(self, user_id: str, use_case: str) -> AIUseCaseModelSelection | None:
        result = await self.db.execute(
            select(AIUseCaseModelSelection).where(
                AIUseCaseModelSelection.user_id == user_id,
                AIUseCaseModelSelection.use_case == use_case,
            )
        )
        return result.scalar_one_or_none()

    async def list_selections(self, user_id: str) -> list[AIUseCaseModelSelection]:
        result = await self.db.execute(
            select(AIUseCaseModelSelection).where(AIUseCaseModelSelection.user_id == user_id)
        )
        return list(result.scalars().all())

    async def set_selection(
        self, user_id: str, use_case: str, provider: str, model: str
    ) -> AIUseCaseModelSelection:
        now = datetime.now(timezone.utc)
        open_history = await self.db.execute(
            select(AIUseCaseModelSelectionHistory).where(
                AIUseCaseModelSelectionHistory.user_id == user_id,
                AIUseCaseModelSelectionHistory.use_case == use_case,
                AIUseCaseModelSelectionHistory.effective_to.is_(None),
            )
        )
        current_open = open_history.scalar_one_or_none()
        if current_open is not None:
            if current_open.provider == provider and current_open.model == model:
                existing = await self.get_selection(user_id, use_case)
                if existing is not None:
                    return existing
            else:
                current_open.effective_to = now

        self.db.add(
            AIUseCaseModelSelectionHistory(
                user_id=user_id,
                use_case=use_case,
                provider=provider,
                model=model,
                effective_from=now,
                effective_to=None,
            )
        )

        existing = await self.get_selection(user_id, use_case)
        if existing is None:
            existing = AIUseCaseModelSelection(
                user_id=user_id,
                use_case=use_case,
                provider=provider,
                model=model,
            )
            self.db.add(existing)
        else:
            existing.provider = provider
            existing.model = model
            existing.updated_at = now

        await self.db.flush()
        await self.db.refresh(existing)
        return existing

    async def list_history(
        self, user_id: str, use_case: str
    ) -> list[AIUseCaseModelSelectionHistory]:
        result = await self.db.execute(
            select(AIUseCaseModelSelectionHistory)
            .where(
                AIUseCaseModelSelectionHistory.user_id == user_id,
                AIUseCaseModelSelectionHistory.use_case == use_case,
            )
            .order_by(AIUseCaseModelSelectionHistory.effective_from.desc())
        )
        return list(result.scalars().all())


def parse_embedding(raw: str | None) -> list[float] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [float(x) for x in data]
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return None


def serialize_embedding(vec: list[float]) -> str:
    return json.dumps(vec)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
