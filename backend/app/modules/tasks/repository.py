from datetime import datetime, time, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.tasks.models import Task, TaskAssignment
from app.modules.tasks.schemas import TaskCreate, TaskUpdate
from app.modules.tasks.status_utils import normalize_task_status

_INCOMPLETE_STATUSES = ("pending", "in_progress", "hold", "delayed")


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _not_deleted(self):
        return Task.deleted_at.is_(None)

    async def list_tasks(
        self,
        user_id: str,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        due_today: bool = False,
        has_due_date: bool | None = None,
        overdue: bool = False,
        due_later: bool = False,
        exclude_due_today: bool = False,
        incomplete_only: bool = False,
        search: str | None = None,
        parent_only: bool = True,
        scope: str = "owned",
        include_archived: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        q = select(Task).options(selectinload(Task.subtasks)).where(self._not_deleted())
        if not include_archived:
            q = q.where(Task.archived_at.is_(None))
        # Inbox: include subtasks assigned to me; exclude work I already own.
        effective_parent_only = False if scope == "assigned_to_me" else parent_only
        if effective_parent_only:
            q = q.where(Task.parent_id.is_(None))

        if scope == "owned":
            q = q.where(Task.user_id == user_id)
        elif scope == "assigned_to_me":
            q = q.join(TaskAssignment, TaskAssignment.task_id == Task.id).where(
                TaskAssignment.assignee_user_id == user_id,
                TaskAssignment.status.in_(("pending", "accepted")),
                Task.user_id != user_id,
            )
        elif scope == "all":
            q = q.outerjoin(TaskAssignment, TaskAssignment.task_id == Task.id).where(
                or_(
                    Task.user_id == user_id,
                    (TaskAssignment.assignee_user_id == user_id)
                    & (TaskAssignment.status.in_(("pending", "accepted"))),
                )
            )
        else:
            q = q.where(Task.user_id == user_id)

        if status:
            q = q.where(Task.status == normalize_task_status(status))
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
        if has_due_date is True:
            q = q.where(Task.due_date.is_not(None))
        elif has_due_date is False:
            q = q.where(Task.due_date.is_(None))
        if overdue:
            today_start, _ = self._today_bounds()
            q = q.where(
                Task.due_date.is_not(None),
                Task.due_date < today_start,
                Task.status.in_(_INCOMPLETE_STATUSES),
            )
        if due_later:
            _, today_end = self._today_bounds()
            q = q.where(Task.due_date.is_not(None), Task.due_date > today_end)
        if exclude_due_today:
            today_start, today_end = self._today_bounds()
            q = q.where(
                or_(
                    Task.due_date.is_(None),
                    Task.due_date < today_start,
                    Task.due_date > today_end,
                )
            )
        if incomplete_only:
            q = q.where(Task.status.in_(_INCOMPLETE_STATUSES))
        if search:
            term = f"%{search.lower()}%"
            q = q.where(or_(Task.title.ilike(term), Task.description.ilike(term)))

        count_q = select(func.count()).select_from(q.order_by(None).distinct().subquery())
        total = (await self.db.execute(count_q)).scalar_one()

        q = q.order_by(Task.due_date.asc().nullslast(), Task.updated_at.desc()).distinct()
        if offset:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().unique().all()), int(total)

    async def get_today_for_dashboard(self, user_id: str, limit: int = 10) -> list[Task]:
        today_start, today_end = self._today_bounds()
        result = await self.db.execute(
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.parent_id.is_(None),
                Task.deleted_at.is_(None),
                Task.archived_at.is_(None),
                Task.status.in_(("pending", "in_progress", "hold", "delayed")),
                Task.due_date.is_not(None),
                Task.due_date >= today_start,
                Task.due_date <= today_end,
            )
            .order_by(Task.priority.desc(), Task.due_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, task_id: str) -> Task | None:
        """Owner-scoped get (backward compatible)."""
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id, Task.user_id == user_id, Task.deleted_at.is_(None))
            .options(selectinload(Task.subtasks))
        )
        return result.scalar_one_or_none()

    async def get_by_id_any(self, task_id: str) -> Task | None:
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id, Task.deleted_at.is_(None))
            .options(selectinload(Task.subtasks), selectinload(Task.assignments))
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
            version=1,
        )
        task.tags = data.tags
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task, ["subtasks"])
        return task

    async def update(self, task: Task, data: TaskUpdate) -> Task:
        payload = data.model_dump(exclude_unset=True)
        payload.pop("version", None)
        payload.pop("status_reason", None)
        tags = payload.pop("tags", None)
        status_val = payload.pop("status", None)
        for key, value in payload.items():
            setattr(task, key, value)
        if tags is not None:
            task.tags = tags
        if status_val is not None:
            task.status = status_val
            if status_val == "completed":
                task.completed_at = datetime.now(timezone.utc)
            elif status_val in ("pending", "in_progress", "hold", "delayed") and task.completed_at:
                task.completed_at = None
        task.version = (task.version or 1) + 1
        await self.db.flush()
        await self.db.refresh(task, ["subtasks"])
        return task

    async def complete(self, task: Task) -> Task:
        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)
        task.version = (task.version or 1) + 1
        await self.db.flush()
        await self.db.refresh(task, ["subtasks"])
        return task

    async def soft_delete(self, task: Task) -> None:
        now = datetime.now(timezone.utc)
        task.deleted_at = now
        task.version = (task.version or 1) + 1
        # Cascade soft-delete subtasks
        result = await self.db.execute(
            select(Task).where(Task.parent_id == task.id, Task.deleted_at.is_(None))
        )
        for sub in result.scalars().all():
            sub.deleted_at = now
        await self.db.flush()

    async def archive(self, task: Task) -> Task:
        task.archived_at = datetime.now(timezone.utc)
        task.version = (task.version or 1) + 1
        await self.db.flush()
        await self.db.refresh(task, ["subtasks"])
        return task

    async def restore(self, task: Task) -> Task:
        task.archived_at = None
        task.version = (task.version or 1) + 1
        await self.db.flush()
        await self.db.refresh(task, ["subtasks"])
        return task

    def _today_bounds(self) -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
        end = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)
        return start, end

    async def get_stats(self, user_id: str) -> tuple[int, int]:
        from datetime import date, timedelta

        today_start, today_end = self._today_bounds()
        base = (
            Task.user_id == user_id,
            Task.parent_id.is_(None),
            self._not_deleted(),
            Task.completed_at.is_not(None),
        )

        completed_today = (
            await self.db.execute(
                select(func.count()).select_from(Task).where(
                    *base,
                    Task.completed_at >= today_start,
                    Task.completed_at <= today_end,
                )
            )
        ).scalar_one()

        rows = await self.db.execute(
            select(Task.completed_at).where(*base).order_by(Task.completed_at.desc()).limit(500)
        )
        completion_dates: set[date] = set()
        for (completed_at,) in rows.all():
            if completed_at is not None:
                completion_dates.add(completed_at.date())

        today = today_start.date()
        streak = 0
        cursor = today if today in completion_dates else today - timedelta(days=1)
        while cursor in completion_dates:
            streak += 1
            cursor -= timedelta(days=1)

        return int(completed_today), streak
