from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import TASK_COMPLETED, TASK_CREATED, TASK_STATUS_CHANGED, EntityCreated, event_bus
from app.modules.tasks.activity_service import ActivityService
from app.modules.tasks.assignment_service import AssignmentService, load_task_for_actor
from app.modules.tasks.collaboration_service import CollaborationService
from app.modules.tasks.models import TaskStatusHistory
from app.modules.tasks.permissions import TaskPermissions
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import SubtaskResponse, TaskCreate, TaskListItem, TaskResponse, TaskUpdate
from app.modules.tasks.status_service import StatusService


class TaskService:
    def __init__(self, db: AsyncSession):
        self.repo = TaskRepository(db)
        self.db = db
        self.activity = ActivityService(db)
        self.assignments = AssignmentService(db)
        self.status_svc = StatusService(db)
        self.collab = CollaborationService(db)
        self.perms = TaskPermissions(db)

    async def _to_response(self, task, user_id: str) -> TaskResponse:
        assignment = await self.assignments.get_active(task.id)
        role = await self.perms.resolve_role(user_id, task)
        assignee_username = None
        if assignment:
            user = await self.assignments.auth.get_by_id(assignment.assignee_user_id)
            assignee_username = user.username if user else None
        subtasks: list[SubtaskResponse] = []
        for s in task.subtasks or []:
            if s.deleted_at is not None:
                continue
            sa = await self.assignments.get_active(s.id)
            suname = None
            if sa:
                su = await self.assignments.auth.get_by_id(sa.assignee_user_id)
                suname = su.username if su else None
            subtasks.append(
                SubtaskResponse(
                    id=s.id,
                    title=s.title,
                    status=s.status,
                    priority=s.priority,
                    completed_at=s.completed_at,
                    assigned_to=sa.assignee_user_id if sa else None,
                    assignment_status=sa.status if sa else None,
                    assignee_username=suname,
                )
            )
        return TaskResponse.from_model(
            task,
            assignment=assignment,
            permissions=self.perms.permission_flags(role),
            assignee_username=assignee_username,
            subtasks=subtasks,
        )

    async def list_tasks(
        self,
        user_id: str,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        due_today: bool = False,
        search: str | None = None,
        scope: str = "owned",
        include_archived: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[TaskListItem], int]:
        tasks, total = await self.repo.list_tasks(
            user_id,
            status=status,
            priority=priority,
            category=category,
            due_today=due_today,
            search=search,
            scope=scope,
            include_archived=include_archived,
            limit=limit,
            offset=offset,
        )
        items: list[TaskListItem] = []
        for t in tasks:
            active = await self.assignments.get_active(t.id)
            visible_subs = [s for s in t.subtasks if s.deleted_at is None]
            items.append(
                TaskListItem(
                    id=t.id,
                    title=t.title,
                    status=t.status,
                    priority=t.priority,
                    category=t.category,
                    tags=t.tags,
                    due_date=t.due_date,
                    updated_at=t.updated_at,
                    goal_id=t.goal_id,
                    subtask_count=len(visible_subs),
                    completed_subtasks=sum(1 for s in visible_subs if s.status == "completed"),
                    assigned_to=active.assignee_user_id if active else None,
                    assignment_status=active.status if active else None,
                    archived_at=t.archived_at,
                )
            )
        return items, total

    async def get_task(self, user_id: str, task_id: str) -> TaskResponse:
        task = await load_task_for_actor(self.db, task_id, user_id)
        return await self._to_response(task, user_id)

    async def create_task(self, user_id: str, data: TaskCreate) -> TaskResponse:
        if data.parent_id:
            parent = await self.repo.get_by_id(user_id, data.parent_id)
            if parent is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent task not found")
        task = await self.repo.create(user_id, data)
        await self.activity.log(task.id, user_id, "create", field="title", new_value=task.title)
        self.db.add(
            TaskStatusHistory(
                task_id=task.id,
                from_status=None,
                to_status=task.status,
                changed_by_user_id=user_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()

        if data.tags:
            await self.collab.sync_tags_from_json(task, user_id, data.tags)

        # Default self-assign OR explicit assignee
        if data.assignee_user_id or data.assignee_username:
            await self.assignments.assign(
                task,
                user_id,
                assignee_user_id=data.assignee_user_id,
                assignee_username=data.assignee_username,
            )
        else:
            await self.assignments.create_self_assignment(task, user_id)

        due = task.due_date.date().isoformat() if task.due_date else None
        await event_bus.emit(
            self.db,
            EntityCreated(
                event_type=TASK_CREATED,
                user_id=user_id,
                entity_id=task.id,
                title=task.title,
                when=due,
                module="tasks",
            ),
        )
        refreshed = await self.repo.get_by_id_any(task.id)
        assert refreshed is not None
        return await self._to_response(refreshed, user_id)

    async def update_task(self, user_id: str, task_id: str, data: TaskUpdate) -> TaskResponse:
        task = await load_task_for_actor(self.db, task_id, user_id)
        payload = data.model_dump(exclude_unset=True)

        # Optimistic concurrency
        if data.version is not None and data.version != (task.version or 1):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Version conflict")

        # Owner-only field edits
        owner_fields = {"title", "description", "priority", "category", "tags", "due_date", "goal_id", "recurrence"}
        if owner_fields & set(payload.keys()):
            await self.perms.require(user_id, task, "edit")

        if "status" in payload and payload["status"] is not None:
            await self.perms.require(user_id, task, "change_status")
            old_status = task.status
            await self.status_svc.change_status(
                task, user_id, payload["status"], reason=data.status_reason
            )
            if payload["status"] == "completed":
                await self.assignments.mark_completed_for_task(task)
                await event_bus.emit(
                    self.db,
                    EntityCreated(
                        event_type=TASK_COMPLETED,
                        user_id=task.user_id,
                        entity_id=task.id,
                        title=task.title,
                        module="tasks",
                    ),
                )
            elif old_status != payload["status"]:
                await event_bus.emit(
                    self.db,
                    EntityCreated(
                        event_type=TASK_STATUS_CHANGED,
                        user_id=task.user_id,
                        entity_id=task.id,
                        title=f"{task.title}: {old_status} → {payload['status']}",
                        module="tasks",
                    ),
                )
            # Remove status from remaining update to avoid double-apply
            data = TaskUpdate(**{k: v for k, v in payload.items() if k not in ("status", "status_reason", "version")})
            if data.model_dump(exclude_unset=True):
                if "tags" in data.model_dump(exclude_unset=True):
                    await self.collab.sync_tags_from_json(task, user_id, data.tags or [])
                await self.repo.update(task, data)
        else:
            dump = data.model_dump(exclude_unset=True)
            if "tags" in dump:
                await self.collab.sync_tags_from_json(task, user_id, data.tags or [])
            # Log field changes
            for field in ("title", "priority", "due_date", "category"):
                if field in dump:
                    old = getattr(task, field)
                    await self.activity.log(
                        task.id,
                        user_id,
                        "update",
                        field=field,
                        old_value=str(old) if old is not None else None,
                        new_value=str(dump[field]) if dump[field] is not None else None,
                    )
            updated = await self.repo.update(task, data)
            task = updated

        refreshed = await self.repo.get_by_id_any(task.id)
        assert refreshed is not None
        return await self._to_response(refreshed, user_id)

    async def complete_task(self, user_id: str, task_id: str) -> TaskResponse:
        task = await load_task_for_actor(self.db, task_id, user_id)
        await self.perms.require(user_id, task, "change_status")
        await self.status_svc.change_status(task, user_id, "completed")
        await self.assignments.mark_completed_for_task(task)
        await self.activity.log(task.id, user_id, "complete")
        await event_bus.emit(
            self.db,
            EntityCreated(
                event_type=TASK_COMPLETED,
                user_id=task.user_id,
                entity_id=task.id,
                title=task.title,
                module="tasks",
            ),
        )
        refreshed = await self.repo.get_by_id_any(task.id)
        assert refreshed is not None
        return await self._to_response(refreshed, user_id)

    async def delete_task(self, user_id: str, task_id: str) -> None:
        task = await load_task_for_actor(self.db, task_id, user_id)
        await self.perms.require(user_id, task, "delete")
        await self.activity.log(task.id, user_id, "delete")
        await self.repo.soft_delete(task)

    async def archive_task(self, user_id: str, task_id: str) -> TaskResponse:
        task = await load_task_for_actor(self.db, task_id, user_id)
        await self.perms.require(user_id, task, "archive")
        await self.repo.archive(task)
        await self.activity.log(task.id, user_id, "archive")
        return await self._to_response(task, user_id)

    async def restore_task(self, user_id: str, task_id: str) -> TaskResponse:
        task = await load_task_for_actor(self.db, task_id, user_id)
        await self.perms.require(user_id, task, "archive")
        await self.repo.restore(task)
        await self.activity.log(task.id, user_id, "restore")
        return await self._to_response(task, user_id)
