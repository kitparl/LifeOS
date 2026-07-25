from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import GOAL_CREATED, GOAL_MILESTONE_ADDED, EntityCreated, event_bus
from app.modules.goals.models import SUGGESTED_GOAL_CATEGORIES, Goal
from app.modules.goals.repository import GoalRepository, is_goal_missed
from app.modules.goals.schemas import (
    GoalCreate,
    GoalListItem,
    GoalResponse,
    GoalUpdate,
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
)


class GoalService:
    def __init__(self, db: AsyncSession):
        self.repo = GoalRepository(db)

    def _to_list_item(self, g: Goal) -> GoalListItem:
        return GoalListItem(
            id=g.id,
            title=g.title,
            category=g.category,
            status=g.status,
            period=getattr(g, "period", None) or "yearly",
            progress=g.progress,
            target_date=g.target_date,
            period_start=getattr(g, "period_start", None),
            period_end=getattr(g, "period_end", None),
            updated_at=g.updated_at,
            milestone_count=len(g.milestones),
            completed_milestones=sum(1 for m in g.milestones if m.completed),
            is_missed=is_goal_missed(g),
        )

    def _to_response(self, goal: Goal) -> GoalResponse:
        data = GoalResponse.model_validate(goal)
        data.is_missed = is_goal_missed(goal)
        if not data.period:
            data.period = "yearly"
        return data

    async def list_goals(
        self,
        user_id: str,
        category: str | None = None,
        status: str | None = None,
        period: str | None = None,
        missed: bool | None = None,
    ) -> list[GoalListItem]:
        goals = await self.repo.list_goals(user_id, category, status, period)
        items = [self._to_list_item(g) for g in goals]
        if missed is True:
            items = [i for i in items if i.is_missed]
        elif missed is False:
            items = [i for i in items if not i.is_missed]
        return items

    async def list_categories(self, user_id: str) -> list[str]:
        """Suggested defaults + user-created, de-duplicated (CI) and sorted."""
        stored = await self.repo.list_category_names(user_id)
        seen: dict[str, str] = {}
        for name in [*SUGGESTED_GOAL_CATEGORIES, *stored]:
            key = name.strip().lower()
            if key and key not in seen:
                seen[key] = name.strip()
        return sorted(seen.values(), key=str.lower)

    async def create_category(self, user_id: str, name: str) -> str:
        clean = name.strip()
        if not clean:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name required")
        await self.repo.ensure_category(user_id, clean)
        return clean

    async def get_goal(self, user_id: str, goal_id: str) -> GoalResponse:
        goal = await self.repo.get_by_id(user_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        return self._to_response(goal)

    async def create_goal(self, user_id: str, data: GoalCreate) -> GoalResponse:
        goal = await self.repo.create(user_id, data)
        target = goal.target_date.date().isoformat() if goal.target_date else None
        await event_bus.emit(
            self.repo.db,
            EntityCreated(
                event_type=GOAL_CREATED,
                user_id=user_id,
                entity_id=goal.id,
                title=goal.title,
                when=target,
                module="goals",
            ),
        )
        return self._to_response(goal)

    async def update_goal(self, user_id: str, goal_id: str, data: GoalUpdate) -> GoalResponse:
        goal = await self.repo.get_by_id(user_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        updated = await self.repo.update(goal, data)
        return self._to_response(updated)

    async def archive_goal(self, user_id: str, goal_id: str) -> GoalResponse:
        goal = await self.repo.get_by_id(user_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        archived = await self.repo.archive(goal)
        return self._to_response(archived)

    async def delete_goal(self, user_id: str, goal_id: str) -> None:
        goal = await self.repo.get_by_id(user_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        await self.repo.delete(goal)

    async def add_milestone(self, user_id: str, goal_id: str, data: MilestoneCreate) -> MilestoneResponse:
        goal = await self.repo.get_by_id(user_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        milestone = await self.repo.add_milestone(goal, data)
        await event_bus.emit(
            self.repo.db,
            EntityCreated(
                event_type=GOAL_MILESTONE_ADDED,
                user_id=user_id,
                entity_id=milestone.id,
                title=f"{goal.title}: {milestone.title}",
                when=None,
                module="goals",
            ),
        )
        return MilestoneResponse.model_validate(milestone)

    async def update_milestone(
        self, user_id: str, goal_id: str, milestone_id: str, data: MilestoneUpdate
    ) -> MilestoneResponse:
        goal = await self.repo.get_by_id(user_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        milestone = await self.repo.get_milestone(goal_id, milestone_id)
        if milestone is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")
        updated = await self.repo.update_milestone(milestone, data)
        return MilestoneResponse.model_validate(updated)

    async def delete_milestone(self, user_id: str, goal_id: str, milestone_id: str) -> None:
        goal = await self.repo.get_by_id(user_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        milestone = await self.repo.get_milestone(goal_id, milestone_id)
        if milestone is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")
        await self.repo.delete_milestone(milestone)
