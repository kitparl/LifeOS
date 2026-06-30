from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.goals.repository import GoalRepository
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

    async def list_goals(
        self, user_id: str, category: str | None = None, status: str | None = None
    ) -> list[GoalListItem]:
        goals = await self.repo.list_goals(user_id, category, status)
        return [
            GoalListItem(
                id=g.id,
                title=g.title,
                category=g.category,
                status=g.status,
                progress=g.progress,
                target_date=g.target_date,
                updated_at=g.updated_at,
                milestone_count=len(g.milestones),
                completed_milestones=sum(1 for m in g.milestones if m.completed),
            )
            for g in goals
        ]

    async def get_goal(self, user_id: str, goal_id: str) -> GoalResponse:
        goal = await self.repo.get_by_id(user_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        return GoalResponse.model_validate(goal)

    async def create_goal(self, user_id: str, data: GoalCreate) -> GoalResponse:
        goal = await self.repo.create(user_id, data)
        return GoalResponse.model_validate(goal)

    async def update_goal(self, user_id: str, goal_id: str, data: GoalUpdate) -> GoalResponse:
        goal = await self.repo.get_by_id(user_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        updated = await self.repo.update(goal, data)
        return GoalResponse.model_validate(updated)

    async def archive_goal(self, user_id: str, goal_id: str) -> GoalResponse:
        goal = await self.repo.get_by_id(user_id, goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        archived = await self.repo.archive(goal)
        return GoalResponse.model_validate(archived)

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
