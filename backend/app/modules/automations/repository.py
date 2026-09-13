from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.modules.automations.models import AutomationRule
from app.modules.automations.schemas import AutomationCreate, AutomationUpdate


class AutomationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_rules(
        self, user_id: str, limit: int | None = None, offset: int = 0
    ) -> tuple[list[AutomationRule], int]:
        q = (
            select(AutomationRule)
            .where(AutomationRule.user_id == user_id)
            .order_by(AutomationRule.created_at.desc())
        )
        if limit is None:
            result = await self.db.execute(q)
            rows = list(result.scalars().all())
            return rows, len(rows)
        return await paginate(self.db, q, Pagination(limit=limit, offset=offset))

    async def get_by_id(self, user_id: str, rule_id: str) -> AutomationRule | None:
        result = await self.db.execute(
            select(AutomationRule).where(AutomationRule.id == rule_id, AutomationRule.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: AutomationCreate) -> AutomationRule:
        rule = AutomationRule(user_id=user_id, **data.model_dump())
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def update(self, rule: AutomationRule, data: AutomationUpdate) -> AutomationRule:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(rule, key, value)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def delete(self, rule: AutomationRule) -> None:
        await self.db.delete(rule)

    async def mark_run(self, rule: AutomationRule) -> None:
        rule.last_run_at = datetime.now(timezone.utc)
        await self.db.flush()
