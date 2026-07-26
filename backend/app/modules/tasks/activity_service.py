"""Append-only activity audit log (SECURITY-13)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tasks.models import TaskActivityLog


class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        task_id: str,
        actor_user_id: str,
        action: str,
        *,
        field: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        metadata: dict | None = None,
    ) -> TaskActivityLog:
        row = TaskActivityLog(
            task_id=task_id,
            actor_user_id=actor_user_id,
            action=action,
            field=field,
            old_value=old_value,
            new_value=new_value,
            metadata_json=json.dumps(metadata) if metadata else None,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def list_for_task(
        self, task_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[TaskActivityLog]:
        result = await self.db.execute(
            select(TaskActivityLog)
            .where(TaskActivityLog.task_id == task_id)
            .order_by(TaskActivityLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
