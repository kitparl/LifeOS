from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.tasks.schemas import TaskCreate, TaskListItem, TaskResponse, TaskUpdate
from app.modules.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskListItem])
async def list_tasks(
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    category: str | None = Query(default=None),
    due_today: bool = Query(default=False),
    search: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).list_tasks(
        user.id, status=status, priority=priority, category=category, due_today=due_today, search=search
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).create_task(user.id, data)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).get_task(user.id, task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).update_task(user.id, task_id, data)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).complete_task(user.id, task_id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await TaskService(db).delete_task(user.id, task_id)
