import json
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.automations.models import AutomationRule
from app.modules.automations.schemas import AutomationCreate, AutomationUpdate
from app.modules.finance.models import FinanceBudget, FinanceTransaction
from app.modules.journal.models import JournalEntry
from app.modules.running.models import Run


class AutomationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_rules(self, user_id: str) -> list[AutomationRule]:
        result = await self.db.execute(
            select(AutomationRule).where(AutomationRule.user_id == user_id).order_by(AutomationRule.created_at.desc())
        )
        return list(result.scalars().all())

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
        rule.last_run_at = datetime.now(UTC)
        await self.db.flush()
