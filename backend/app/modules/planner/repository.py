from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezone import utc_now
from app.modules.planner.models import PlannerNode


class PlannerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_nodes(self, user_id: str) -> list[PlannerNode]:
        result = await self.db.execute(
            select(PlannerNode)
            .where(PlannerNode.user_id == user_id, PlannerNode.deleted_at.is_(None))
            .order_by(PlannerNode.parent_id.asc(), PlannerNode.order_index.asc(), PlannerNode.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, node_id: str) -> PlannerNode | None:
        result = await self.db.execute(
            select(PlannerNode).where(
                PlannerNode.id == node_id,
                PlannerNode.user_id == user_id,
                PlannerNode.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_children(self, user_id: str, parent_id: str | None) -> list[PlannerNode]:
        """Non-deleted siblings under `parent_id` (None = top level), in display order."""
        parent_match = (
            PlannerNode.parent_id.is_(None) if parent_id is None else PlannerNode.parent_id == parent_id
        )
        result = await self.db.execute(
            select(PlannerNode)
            .where(PlannerNode.user_id == user_id, PlannerNode.deleted_at.is_(None), parent_match)
            .order_by(PlannerNode.order_index.asc(), PlannerNode.created_at.asc())
        )
        return list(result.scalars().all())

    async def count_children(self, user_id: str, parent_id: str | None) -> int:
        parent_match = (
            PlannerNode.parent_id.is_(None) if parent_id is None else PlannerNode.parent_id == parent_id
        )
        result = await self.db.execute(
            select(func.count(PlannerNode.id)).where(
                PlannerNode.user_id == user_id, PlannerNode.deleted_at.is_(None), parent_match
            )
        )
        return result.scalar_one()

    async def add(self, node: PlannerNode) -> PlannerNode:
        self.db.add(node)
        await self.db.flush()
        await self.db.refresh(node)
        return node

    async def save_content_if_revision(self, user_id: str, node_id: str, content: str, base_revision: int) -> bool:
        """Atomically store `content` and bump the revision; False if `base_revision` is stale."""
        result = await self.db.execute(
            update(PlannerNode)
            .where(
                PlannerNode.id == node_id,
                PlannerNode.user_id == user_id,
                PlannerNode.deleted_at.is_(None),
                PlannerNode.revision == base_revision,
            )
            .values(content=content, revision=base_revision + 1)
            .execution_options(synchronize_session="fetch")
        )
        return result.rowcount == 1

    async def flush(self) -> None:
        await self.db.flush()

    async def soft_delete(self, nodes: list[PlannerNode]) -> None:
        now = utc_now()
        for node in nodes:
            node.deleted_at = now
        await self.db.flush()
