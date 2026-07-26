"""Watchers, notes, and normalized tags."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.tasks.activity_service import ActivityService
from app.modules.tasks.models import Task, TaskNote, TaskTag, TaskTagLink, TaskWatcher
from app.modules.tasks.permissions import TaskPermissions


class CollaborationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.activity = ActivityService(db)
        self.perms = TaskPermissions(db)
        self.auth = UserRepository(db)

    # --- Watchers ---

    async def list_watchers(self, task: Task) -> list[tuple[TaskWatcher, User | None]]:
        result = await self.db.execute(
            select(TaskWatcher).where(TaskWatcher.task_id == task.id)
        )
        watchers = list(result.scalars().all())
        out: list[tuple[TaskWatcher, User | None]] = []
        for w in watchers:
            u = await self.auth.get_by_id(w.user_id)
            out.append((w, u))
        return out

    async def add_watcher(
        self,
        task: Task,
        actor_id: str,
        *,
        username: str | None = None,
        user_id: str | None = None,
    ) -> TaskWatcher:
        await self.perms.require(actor_id, task, "manage_watchers")
        if username:
            user = await self.auth.get_by_username(username)
            if user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            user_id = user.id
        if not user_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="username or user_id required")
        existing = await self.db.execute(
            select(TaskWatcher).where(TaskWatcher.task_id == task.id, TaskWatcher.user_id == user_id)
        )
        row = existing.scalar_one_or_none()
        if row:
            return row
        row = TaskWatcher(task_id=task.id, user_id=user_id)
        self.db.add(row)
        await self.db.flush()
        await self.activity.log(task.id, actor_id, "watcher_add", field="watcher", new_value=user_id)
        return row

    async def remove_watcher(self, task: Task, actor_id: str, watcher_user_id: str) -> None:
        await self.perms.require(actor_id, task, "manage_watchers")
        result = await self.db.execute(
            select(TaskWatcher).where(
                TaskWatcher.task_id == task.id, TaskWatcher.user_id == watcher_user_id
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watcher not found")
        await self.db.delete(row)
        await self.db.flush()
        await self.activity.log(task.id, actor_id, "watcher_remove", field="watcher", old_value=watcher_user_id)

    # --- Notes ---

    async def list_notes(self, task: Task) -> list[TaskNote]:
        result = await self.db.execute(
            select(TaskNote)
            .where(TaskNote.task_id == task.id, TaskNote.deleted_at.is_(None))
            .order_by(TaskNote.created_at.desc())
        )
        return list(result.scalars().all())

    async def add_note(self, task: Task, actor_id: str, body: str) -> TaskNote:
        await self.perms.require(actor_id, task, "add_note")
        note = TaskNote(task_id=task.id, author_user_id=actor_id, body=body)
        self.db.add(note)
        await self.db.flush()
        await self.activity.log(task.id, actor_id, "note", field="note", new_value=body[:200])
        return note

    async def delete_note(self, task: Task, actor_id: str, note_id: str) -> None:
        result = await self.db.execute(
            select(TaskNote).where(TaskNote.id == note_id, TaskNote.task_id == task.id, TaskNote.deleted_at.is_(None))
        )
        note = result.scalar_one_or_none()
        if note is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        role = await self.perms.resolve_role(actor_id, task)
        if note.author_user_id != actor_id and role.value != "owner":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        note.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.activity.log(task.id, actor_id, "note_delete", field="note", old_value=note_id)

    # --- Tags ---

    async def list_task_tags(self, task: Task) -> list[TaskTag]:
        result = await self.db.execute(
            select(TaskTag)
            .join(TaskTagLink, TaskTagLink.tag_id == TaskTag.id)
            .where(TaskTagLink.task_id == task.id)
            .order_by(TaskTag.name.asc())
        )
        return list(result.scalars().all())

    async def list_user_tags(self, user_id: str) -> list[TaskTag]:
        result = await self.db.execute(
            select(TaskTag).where(TaskTag.user_id == user_id).order_by(TaskTag.name.asc())
        )
        return list(result.scalars().all())

    async def attach_tag(self, task: Task, actor_id: str, name: str) -> TaskTag:
        await self.perms.require(actor_id, task, "manage_tags")
        clean = name.strip().lower()[:64]
        if not clean:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid tag name")
        result = await self.db.execute(
            select(TaskTag).where(TaskTag.user_id == task.user_id, TaskTag.name == clean)
        )
        tag = result.scalar_one_or_none()
        if tag is None:
            tag = TaskTag(user_id=task.user_id, name=clean)
            self.db.add(tag)
            await self.db.flush()
        link_q = await self.db.execute(
            select(TaskTagLink).where(TaskTagLink.task_id == task.id, TaskTagLink.tag_id == tag.id)
        )
        if link_q.scalar_one_or_none() is None:
            self.db.add(TaskTagLink(task_id=task.id, tag_id=tag.id))
            await self.db.flush()
        # Keep tags_json cache in sync
        names = [t.name for t in await self.list_task_tags(task)]
        if clean not in names:
            names.append(clean)
        task.tags = sorted(set(names))
        await self.db.flush()
        await self.activity.log(task.id, actor_id, "tag_add", field="tags", new_value=clean)
        return tag

    async def detach_tag(self, task: Task, actor_id: str, tag_id: str) -> None:
        await self.perms.require(actor_id, task, "manage_tags")
        result = await self.db.execute(
            select(TaskTagLink).where(TaskTagLink.task_id == task.id, TaskTagLink.tag_id == tag_id)
        )
        link = result.scalar_one_or_none()
        if link is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not linked")
        tag_result = await self.db.execute(select(TaskTag).where(TaskTag.id == tag_id))
        tag = tag_result.scalar_one_or_none()
        await self.db.delete(link)
        await self.db.flush()
        names = [t.name for t in await self.list_task_tags(task)]
        task.tags = names
        await self.db.flush()
        await self.activity.log(
            task.id, actor_id, "tag_remove", field="tags", old_value=tag.name if tag else tag_id
        )

    async def sync_tags_from_json(self, task: Task, actor_id: str, tags: list[str]) -> None:
        """Called when TaskUpdate.tags is set — sync normalized tables + cache."""
        clean = sorted({t.strip().lower()[:64] for t in tags if t and t.strip()})
        # Remove links not in clean
        current = await self.list_task_tags(task)
        for tag in current:
            if tag.name not in clean:
                await self.db.execute(
                    select(TaskTagLink).where(TaskTagLink.task_id == task.id, TaskTagLink.tag_id == tag.id)
                )
                link_r = await self.db.execute(
                    select(TaskTagLink).where(TaskTagLink.task_id == task.id, TaskTagLink.tag_id == tag.id)
                )
                link = link_r.scalar_one_or_none()
                if link:
                    await self.db.delete(link)
        await self.db.flush()
        for name in clean:
            result = await self.db.execute(
                select(TaskTag).where(TaskTag.user_id == task.user_id, TaskTag.name == name)
            )
            tag = result.scalar_one_or_none()
            if tag is None:
                tag = TaskTag(user_id=task.user_id, name=name)
                self.db.add(tag)
                await self.db.flush()
            link_r = await self.db.execute(
                select(TaskTagLink).where(TaskTagLink.task_id == task.id, TaskTagLink.tag_id == tag.id)
            )
            if link_r.scalar_one_or_none() is None:
                self.db.add(TaskTagLink(task_id=task.id, tag_id=tag.id))
        task.tags = clean
        await self.db.flush()
