import json
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.automations.models import TRIGGER_TYPES, ACTION_TYPES, AutomationRule
from app.modules.automations.repository import AutomationRepository
from app.modules.automations.schemas import (
    AutomationCreate,
    AutomationEvaluateResponse,
    AutomationResponse,
    AutomationRunResult,
    AutomationUpdate,
)
from app.modules.finance.models import FinanceBudget, FinanceTransaction
from app.modules.journal.models import JournalEntry
from app.modules.notifications.schemas import NotificationCreate
from app.modules.notifications.service import NotificationService
from app.modules.running.models import Run


class AutomationService:
    def __init__(self, db: AsyncSession):
        self.repo = AutomationRepository(db)
        self.notifications = NotificationService(db)

    async def list_rules(self, user_id: str) -> list[AutomationResponse]:
        rules = await self.repo.list_rules(user_id)
        return [AutomationResponse.model_validate(r) for r in rules]

    async def create_rule(self, user_id: str, data: AutomationCreate) -> AutomationResponse:
        if data.trigger_type not in TRIGGER_TYPES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown trigger: {data.trigger_type}")
        if data.action_type not in ACTION_TYPES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown action: {data.action_type}")
        rule = await self.repo.create(user_id, data)
        return AutomationResponse.model_validate(rule)

    async def update_rule(self, user_id: str, rule_id: str, data: AutomationUpdate) -> AutomationResponse:
        rule = await self.repo.get_by_id(user_id, rule_id)
        if not rule:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Automation rule not found")
        updated = await self.repo.update(rule, data)
        return AutomationResponse.model_validate(updated)

    async def delete_rule(self, user_id: str, rule_id: str) -> None:
        rule = await self.repo.get_by_id(user_id, rule_id)
        if not rule:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Automation rule not found")
        await self.repo.delete(rule)

    async def evaluate(self, user_id: str) -> AutomationEvaluateResponse:
        rules = await self.repo.list_rules(user_id)
        results: list[AutomationRunResult] = []
        triggered_count = 0

        for rule in rules:
            if not rule.enabled:
                results.append(AutomationRunResult(
                    rule_id=rule.id, rule_name=rule.name, triggered=False, message="Rule disabled"
                ))
                continue

            fired, msg = await self._check_trigger(user_id, rule)
            action_taken = None
            if fired:
                triggered_count += 1
                action_taken = await self._execute_action(user_id, rule, msg)
                await self.repo.mark_run(rule)

            results.append(AutomationRunResult(
                rule_id=rule.id,
                rule_name=rule.name,
                triggered=fired,
                action_taken=action_taken,
                message=msg,
            ))

        return AutomationEvaluateResponse(
            evaluated=len(rules), triggered=triggered_count, results=results
        )

    async def _check_trigger(self, user_id: str, rule: AutomationRule) -> tuple[bool, str]:
        cond = {}
        if rule.condition_json:
            try:
                cond = json.loads(rule.condition_json)
            except json.JSONDecodeError:
                cond = {}

        if rule.trigger_type == "no_journal_days":
            days = int(cond.get("days", 3))
            since = datetime.now(UTC) - timedelta(days=days)
            count = await self.db.execute(
                select(func.count()).select_from(JournalEntry).where(
                    JournalEntry.user_id == user_id, JournalEntry.created_at >= since
                )
            )
            if int(count.scalar() or 0) == 0:
                return True, f"No journal entries in the last {days} days"
            return False, f"Journal entries found in last {days} days"

        if rule.trigger_type == "budget_exceeded":
            category = cond.get("category", "food")
            budgets = await self.db.execute(
                select(FinanceBudget).where(
                    FinanceBudget.user_id == user_id, FinanceBudget.category == category
                )
            )
            budget = budgets.scalar_one_or_none()
            if not budget:
                return False, f"No budget configured for {category}"
            month_start = date.today().replace(day=1)
            spent = await self.db.execute(
                select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
                    FinanceTransaction.user_id == user_id,
                    FinanceTransaction.txn_type == "expense",
                    FinanceTransaction.category == category,
                    FinanceTransaction.txn_date >= month_start,
                )
            )
            total = float(spent.scalar() or 0)
            if total > float(budget.monthly_limit):
                return True, f"{category} spending {total:.2f} exceeds budget {budget.monthly_limit}"
            return False, f"{category} spending within budget"

        if rule.trigger_type == "running_goal_missed":
            km_target = float(cond.get("weekly_km", 20))
            week_start = date.today() - timedelta(days=7)
            dist = await self.db.execute(
                select(func.coalesce(func.sum(Run.distance_km), 0)).where(
                    Run.user_id == user_id, Run.run_date >= week_start
                )
            )
            total = float(dist.scalar() or 0)
            if total < km_target:
                return True, f"Weekly distance {total:.1f}km below target {km_target}km"
            return False, f"Weekly distance {total:.1f}km meets target"

        if rule.trigger_type == "habit_streak_broken":
            return False, "Habit streak check requires habit-specific config (stub)"

        return False, "Unknown trigger"

    async def _execute_action(self, user_id: str, rule: AutomationRule, msg: str) -> str:
        if rule.action_type == "notify":
            await self.notifications.create(
                user_id,
                NotificationCreate(message=f"Automation '{rule.name}': {msg}", module="automations"),
            )
            return "notification_created"
        if rule.action_type == "generate_report":
            return "report_stub_scheduled"
        if rule.action_type == "telegram":
            return "telegram_stub_sent"
        return "no_action"

    @property
    def db(self):
        return self.repo.db
