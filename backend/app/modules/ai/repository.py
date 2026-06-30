import json
import math

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import ContentEmbedding


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
