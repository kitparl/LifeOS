from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.goals.models import Goal, GoalMilestone
from app.modules.goals.schemas import GoalCreate, GoalUpdate, MilestoneCreate, MilestoneUpdate


class GoalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_goals(
        self,
        user_id: str,
        category: str | None = None,
        status: str | None = None,
    ) -> list[Goal]:
        q = select(Goal).where(Goal.user_id == user_id).options(selectinload(Goal.milestones))
        if category:
            q = q.where(Goal.category == category)
        if status:
            q = q.where(Goal.status == status)
        q = q.order_by(Goal.updated_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().unique().all())

    async def get_active_for_dashboard(self, user_id: str, limit: int = 5) -> list[Goal]:
        result = await self.db.execute(
            select(Goal)
            .where(Goal.user_id == user_id, Goal.status == "active")
            .order_by(Goal.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, goal_id: str) -> Goal | None:
        result = await self.db.execute(
            select(Goal)
            .where(Goal.id == goal_id, Goal.user_id == user_id)
            .options(selectinload(Goal.milestones))
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: GoalCreate) -> Goal:
        goal = Goal(
            user_id=user_id,
            title=data.title,
            description=data.description,
            category=data.category,
            progress=data.progress,
            notes=data.notes,
            target_date=data.target_date,
            parent_id=data.parent_id,
        )
        self.db.add(goal)
        await self.db.flush()
        await self.db.refresh(goal, ["milestones"])
        return goal

    async def update(self, goal: Goal, data: GoalUpdate) -> Goal:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(goal, field, value)
        if data.status == "completed" and goal.progress < 100:
            goal.progress = 100
        await self.db.flush()
        await self.db.refresh(goal, ["milestones"])
        return goal

    async def archive(self, goal: Goal) -> Goal:
        goal.status = "archived"
        goal.archived_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(goal, ["milestones"])
        return goal

    async def delete(self, goal: Goal) -> None:
        await self.db.delete(goal)
        await self.db.flush()

    async def add_milestone(self, goal: Goal, data: MilestoneCreate) -> GoalMilestone:
        sort_order = len(goal.milestones)
        milestone = GoalMilestone(goal_id=goal.id, title=data.title, sort_order=sort_order)
        self.db.add(milestone)
        await self._recalculate_progress(goal)
        await self.db.flush()
        await self.db.refresh(milestone)
        return milestone

    async def update_milestone(self, milestone: GoalMilestone, data: MilestoneUpdate) -> GoalMilestone:
        if data.title is not None:
            milestone.title = data.title
        if data.completed is not None:
            milestone.completed = data.completed
            milestone.completed_at = datetime.now(UTC) if data.completed else None
        goal = await self.get_by_id_raw(milestone.goal_id)
        if goal:
            await self._recalculate_progress(goal)
        await self.db.flush()
        await self.db.refresh(milestone)
        return milestone

    async def delete_milestone(self, milestone: GoalMilestone) -> None:
        goal_id = milestone.goal_id
        await self.db.delete(milestone)
        await self.db.flush()
        goal = await self.get_by_id_raw(goal_id)
        if goal:
            await self._recalculate_progress(goal)
            await self.db.flush()

    async def get_milestone(self, goal_id: str, milestone_id: str) -> GoalMilestone | None:
        result = await self.db.execute(
            select(GoalMilestone).where(GoalMilestone.id == milestone_id, GoalMilestone.goal_id == goal_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_raw(self, goal_id: str) -> Goal | None:
        result = await self.db.execute(
            select(Goal).where(Goal.id == goal_id).options(selectinload(Goal.milestones))
        )
        return result.scalar_one_or_none()

    async def _recalculate_progress(self, goal: Goal) -> None:
        if not goal.milestones:
            return
        completed = sum(1 for m in goal.milestones if m.completed)
        goal.progress = int((completed / len(goal.milestones)) * 100)
