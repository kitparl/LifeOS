from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import TaskCreate, TaskListItem, TaskResponse, TaskUpdate


class TaskService:
    def __init__(self, db: AsyncSession):
        self.repo = TaskRepository(db)

    async def list_tasks(
        self,
        user_id: str,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        due_today: bool = False,
        search: str | None = None,
    ) -> list[TaskListItem]:
        tasks = await self.repo.list_tasks(
            user_id, status=status, priority=priority, category=category, due_today=due_today, search=search
        )
        return [
            TaskListItem(
                id=t.id,
                title=t.title,
                status=t.status,
                priority=t.priority,
                category=t.category,
                tags=t.tags,
                due_date=t.due_date,
                updated_at=t.updated_at,
                subtask_count=len(t.subtasks),
                completed_subtasks=sum(1 for s in t.subtasks if s.status == "completed"),
            )
            for t in tasks
        ]

    async def get_task(self, user_id: str, task_id: str) -> TaskResponse:
        task = await self.repo.get_by_id(user_id, task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return TaskResponse.from_model(task)

    async def create_task(self, user_id: str, data: TaskCreate) -> TaskResponse:
        if data.parent_id:
            parent = await self.repo.get_by_id(user_id, data.parent_id)
            if parent is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent task not found")
        task = await self.repo.create(user_id, data)
        return TaskResponse.from_model(task)

    async def update_task(self, user_id: str, task_id: str, data: TaskUpdate) -> TaskResponse:
        task = await self.repo.get_by_id(user_id, task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        updated = await self.repo.update(task, data)
        return TaskResponse.from_model(updated)

    async def complete_task(self, user_id: str, task_id: str) -> TaskResponse:
        task = await self.repo.get_by_id(user_id, task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        completed = await self.repo.complete(task)
        return TaskResponse.from_model(completed)

    async def delete_task(self, user_id: str, task_id: str) -> None:
        task = await self.repo.get_by_id(user_id, task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        await self.repo.delete(task)
