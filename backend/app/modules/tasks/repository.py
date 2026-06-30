from datetime import UTC, datetime, time

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.tasks.models import Task
from app.modules.tasks.schemas import TaskCreate, TaskUpdate


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_tasks(
        self,
        user_id: str,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        due_today: bool = False,
        search: str | None = None,
        parent_only: bool = True,
    ) -> list[Task]:
        q = select(Task).where(Task.user_id == user_id).options(selectinload(Task.subtasks))
        if parent_only:
            q = q.where(Task.parent_id.is_(None))
        if status:
            q = q.where(Task.status == status)
        if priority:
            q = q.where(Task.priority == priority)
        if category:
            q = q.where(Task.category == category)
        if due_today:
            today_start, today_end = self._today_bounds()
            q = q.where(
                Task.due_date.is_not(None),
                Task.due_date >= today_start,
                Task.due_date <= today_end,
            )
        if search:
            term = f"%{search.lower()}%"
            q = q.where(or_(Task.title.ilike(term), Task.description.ilike(term)))
        q = q.order_by(Task.due_date.asc().nullslast(), Task.updated_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().unique().all())

    async def get_today_for_dashboard(self, user_id: str, limit: int = 10) -> list[Task]:
        today_start, today_end = self._today_bounds()
        result = await self.db.execute(
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.parent_id.is_(None),
                Task.status.in_(("pending", "in_progress")),
                Task.due_date.is_not(None),
                Task.due_date >= today_start,
                Task.due_date <= today_end,
            )
            .order_by(Task.priority.desc(), Task.due_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, task_id: str) -> Task | None:
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id, Task.user_id == user_id)
            .options(selectinload(Task.subtasks))
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: TaskCreate) -> Task:
        task = Task(
            user_id=user_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            category=data.category,
            due_date=data.due_date,
            parent_id=data.parent_id,
            goal_id=data.goal_id,
            recurrence=data.recurrence,
        )
        task.tags = data.tags
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task, ["subtasks"])
        return task

    async def update(self, task: Task, data: TaskUpdate) -> Task:
        payload = data.model_dump(exclude_unset=True)
        tags = payload.pop("tags", None)
        for key, value in payload.items():
            setattr(task, key, value)
        if tags is not None:
            task.tags = tags
        if data.status == "completed":
            task.completed_at = datetime.now(UTC)
        elif data.status in ("pending", "in_progress") and task.completed_at:
            task.completed_at = None
        await self.db.flush()
        await self.db.refresh(task, ["subtasks"])
        return task

    async def complete(self, task: Task) -> Task:
        task.status = "completed"
        task.completed_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(task, ["subtasks"])
        return task

    async def delete(self, task: Task) -> None:
        await self.db.delete(task)
        await self.db.flush()

    def _today_bounds(self) -> tuple[datetime, datetime]:
        now = datetime.now(UTC)
        start = datetime.combine(now.date(), time.min, tzinfo=UTC)
        end = datetime.combine(now.date(), time.max, tzinfo=UTC)
        return start, end
