"""Repository helpers for scheduled_report_runs audit rows."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.report_models import ScheduledReportRun

logger = logging.getLogger(__name__)


class ReportRunRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_run(
        self,
        *,
        user_id: str,
        job_type: str,
        job_id: str = "",
        connection_id: str | None = None,
        dedupe_key: str | None = None,
        scheduled_for: datetime | None = None,
        status: str = "started",
        skip_reason: str | None = None,
    ) -> ScheduledReportRun:
        """Insert a run row (no unique-key conflict expected for non-dedupe jobs)."""
        run = ScheduledReportRun(
            user_id=user_id,
            connection_id=connection_id,
            job_type=job_type,
            job_id=job_id,
            status=status,
            skip_reason=skip_reason,
            dedupe_key=dedupe_key,
            scheduled_for=scheduled_for,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc) if status != "started" else None,
        )
        self.db.add(run)
        await self.db.flush()
        return run

    async def claim_dedupe(
        self,
        *,
        user_id: str,
        job_type: str,
        dedupe_key: str,
        job_id: str = "",
        connection_id: str | None = None,
        scheduled_for: datetime | None = None,
    ) -> ScheduledReportRun | None:
        """Atomically claim a reminder slot via unique dedupe_key. None = already dispatched."""
        existing = await self.db.execute(
            select(ScheduledReportRun.id).where(ScheduledReportRun.dedupe_key == dedupe_key)
        )
        if existing.scalar_one_or_none() is not None:
            return None

        try:
            async with self.db.begin_nested():
                run = ScheduledReportRun(
                    user_id=user_id,
                    connection_id=connection_id,
                    job_type=job_type,
                    job_id=job_id,
                    status="started",
                    dedupe_key=dedupe_key,
                    scheduled_for=scheduled_for,
                    started_at=datetime.now(timezone.utc),
                )
                self.db.add(run)
                await self.db.flush()
                return run
        except IntegrityError:
            logger.debug("Dedupe race for key=%s", dedupe_key)
            return None

    async def finish_run(
        self,
        run: ScheduledReportRun,
        *,
        status: str,
        skip_reason: str | None = None,
        error: str | None = None,
        sections: dict[str, Any] | None = None,
        message_chars: int | None = None,
    ) -> ScheduledReportRun:
        run.status = status
        run.skip_reason = skip_reason
        run.error = (error or "")[:2000] or None
        if sections is not None:
            run.sections_json = json.dumps(sections)
        run.message_chars = message_chars
        run.finished_at = datetime.now(timezone.utc)
        await self.db.flush()
        return run

    async def list_runs(
        self,
        user_id: str,
        *,
        job_type: str | None = None,
        limit: int = 50,
    ) -> list[ScheduledReportRun]:
        q = (
            select(ScheduledReportRun)
            .where(ScheduledReportRun.user_id == user_id)
            .order_by(ScheduledReportRun.created_at.desc())
            .limit(limit)
        )
        if job_type:
            q = q.where(ScheduledReportRun.job_type == job_type)
        result = await self.db.execute(q)
        return list(result.scalars().all())
