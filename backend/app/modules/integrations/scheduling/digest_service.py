"""Manual digest entry point: delivers the morning scheduled report through the Notifier registry."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.scheduling.scheduled_report_service import ScheduledReportService
from app.modules.integrations.schemas import DigestResponse


class DigestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_digest(self, user_id: str) -> DigestResponse:
        """Manual / scheduled entry: enriched morning report (Cycle 8)."""
        return await ScheduledReportService(self.db).run(user_id, "morning")
