from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.tasks.activity_service import ActivityService
from app.modules.tasks.assignment_service import AssignmentService, load_task_for_actor
from app.modules.tasks.collaboration_service import CollaborationService
from app.modules.tasks.permissions import TaskPermissions
from app.modules.tasks.schemas import (
    ActivityLogResponse,
    AssignRequest,
    AssignmentResponse,
    NoteCreate,
    NoteResponse,
    RejectRequest,
    StatusHistoryResponse,
    TagAttachRequest,
    TagResponse,
    TaskCreate,
    TaskListItem,
    TaskResponse,
    TaskUpdate,
    WatcherCreate,
    WatcherResponse,
)
from app.modules.tasks.service import TaskService
from app.modules.tasks.status_service import StatusService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskListItem])
async def list_tasks(
    response: Response,
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    category: str | None = Query(default=None),
    due_today: bool = Query(default=False),
    search: str | None = Query(default=None),
    scope: str = Query(default="owned", pattern="^(owned|assigned_to_me|all)$"),
    include_archived: bool = Query(default=False),
    limit: int | None = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await TaskService(db).list_tasks(
        user.id,
        status=status_filter,
        priority=priority,
        category=category,
        due_today=due_today,
        search=search,
        scope=scope,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).create_task(user.id, data)


@router.get("/tags", response_model=list[TagResponse])
async def list_my_tags(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tags = await CollaborationService(db).list_user_tags(user.id)
    return [TagResponse.model_validate(t) for t in tags]


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


@router.post("/{task_id}/archive", response_model=TaskResponse)
async def archive_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).archive_task(user.id, task_id)


@router.post("/{task_id}/restore", response_model=TaskResponse)
async def restore_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).restore_task(user.id, task_id)


@router.post("/{task_id}/assign", response_model=AssignmentResponse)
async def assign_task(
    task_id: str,
    data: AssignRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    row = await AssignmentService(db).assign(
        task,
        user.id,
        assignee_user_id=data.assignee_user_id,
        assignee_username=data.assignee_username,
        reason=data.reason,
    )
    return AssignmentResponse.model_validate(row)


@router.get("/{task_id}/assignments", response_model=list[AssignmentResponse])
async def list_assignments(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    await TaskPermissions(db).require(user.id, task, "view")
    rows = await AssignmentService(db).list_for_task(task_id)
    return [AssignmentResponse.model_validate(r) for r in rows]


@router.post("/{task_id}/assignments/{assignment_id}/accept", response_model=AssignmentResponse)
async def accept_assignment(
    task_id: str,
    assignment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    row = await AssignmentService(db).accept(task, assignment_id, user.id)
    return AssignmentResponse.model_validate(row)


@router.post("/{task_id}/assignments/{assignment_id}/reject", response_model=AssignmentResponse)
async def reject_assignment(
    task_id: str,
    assignment_id: str,
    data: RejectRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    row = await AssignmentService(db).reject(
        task, assignment_id, user.id, reason=(data.reason if data else None)
    )
    return AssignmentResponse.model_validate(row)


@router.post("/{task_id}/assignments/{assignment_id}/cancel", response_model=AssignmentResponse)
async def cancel_assignment(
    task_id: str,
    assignment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    row = await AssignmentService(db).cancel(task, assignment_id, user.id)
    return AssignmentResponse.model_validate(row)


@router.get("/{task_id}/status-history", response_model=list[StatusHistoryResponse])
async def status_history(
    task_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    await TaskPermissions(db).require(user.id, task, "view")
    rows = await StatusService(db).list_history(task_id, limit=limit, offset=offset)
    return [StatusHistoryResponse.model_validate(r) for r in rows]


@router.get("/{task_id}/activity", response_model=list[ActivityLogResponse])
async def activity_log(
    task_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    await TaskPermissions(db).require(user.id, task, "view")
    rows = await ActivityService(db).list_for_task(task_id, limit=limit, offset=offset)
    return [ActivityLogResponse.model_validate(r) for r in rows]


@router.get("/{task_id}/watchers", response_model=list[WatcherResponse])
async def list_watchers(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    await TaskPermissions(db).require(user.id, task, "view")
    pairs = await CollaborationService(db).list_watchers(task)
    return [
        WatcherResponse(
            id=w.id,
            task_id=w.task_id,
            user_id=w.user_id,
            username=u.username if u else None,
            display_name=u.display_name if u else None,
            created_at=w.created_at,
        )
        for w, u in pairs
    ]


@router.post("/{task_id}/watchers", response_model=WatcherResponse, status_code=status.HTTP_201_CREATED)
async def add_watcher(
    task_id: str,
    data: WatcherCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    w = await CollaborationService(db).add_watcher(
        task, user.id, username=data.username, user_id=data.user_id
    )
    from app.modules.auth.repository import UserRepository

    u = await UserRepository(db).get_by_id(w.user_id)
    return WatcherResponse(
        id=w.id,
        task_id=w.task_id,
        user_id=w.user_id,
        username=u.username if u else None,
        display_name=u.display_name if u else None,
        created_at=w.created_at,
    )


@router.delete("/{task_id}/watchers/{watcher_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_watcher(
    task_id: str,
    watcher_user_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    await CollaborationService(db).remove_watcher(task, user.id, watcher_user_id)


@router.get("/{task_id}/notes", response_model=list[NoteResponse])
async def list_notes(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    await TaskPermissions(db).require(user.id, task, "view")
    notes = await CollaborationService(db).list_notes(task)
    return [NoteResponse.model_validate(n) for n in notes]


@router.post("/{task_id}/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def add_note(
    task_id: str,
    data: NoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    note = await CollaborationService(db).add_note(task, user.id, data.body)
    return NoteResponse.model_validate(note)


@router.delete("/{task_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    task_id: str,
    note_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    await CollaborationService(db).delete_note(task, user.id, note_id)


@router.get("/{task_id}/tags", response_model=list[TagResponse])
async def list_task_tags(
    task_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    await TaskPermissions(db).require(user.id, task, "view")
    tags = await CollaborationService(db).list_task_tags(task)
    return [TagResponse.model_validate(t) for t in tags]


@router.post("/{task_id}/tags", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def attach_tag(
    task_id: str,
    data: TagAttachRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    tag = await CollaborationService(db).attach_tag(task, user.id, data.name)
    return TagResponse.model_validate(tag)


@router.delete("/{task_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag(
    task_id: str,
    tag_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await load_task_for_actor(db, task_id, user.id)
    await CollaborationService(db).detach_tag(task, user.id, tag_id)
