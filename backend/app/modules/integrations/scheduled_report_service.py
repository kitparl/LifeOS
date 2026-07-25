"""Orchestrate gated scheduled report delivery with audit logging."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.notifier import NotifierMessage
from app.modules.integrations.notifier_registry import build_user_notifier
from app.modules.integrations.report_builders import BUILDERS, SKIP_IF_EMPTY
from app.modules.integrations.report_repository import ReportRunRepository
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import DigestResponse
from app.modules.integrations.telegram_config import TelegramPreferences, parse_preferences
from app.modules.integrations import telegram_templates as tpl

logger = logging.getLogger(__name__)

CRON_JOB_TYPES = ("morning", "midday", "night", "weekly", "ai_briefing")


def _safe_zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name or "Asia/Kolkata")
    except ZoneInfoNotFoundError:
        return ZoneInfo("Asia/Kolkata")


def _pref_enabled(prefs: TelegramPreferences, job_type: str) -> bool:
    return {
        "morning": prefs.morning_enabled,
        "midday": prefs.midday_enabled,
        "night": prefs.night_enabled,
        "weekly": prefs.weekly_enabled,
        "ai_briefing": prefs.ai_briefing_enabled,
    }.get(job_type, False)


def job_id_for(user_id: str, job_type: str) -> str:
    return f"telegram_{job_type}_{user_id}"


class ScheduledReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.runs = ReportRunRepository(db)
        self.integrations = IntegrationRepository(db)

    async def run(self, user_id: str, job_type: str) -> DigestResponse:
        if job_type not in BUILDERS:
            return DigestResponse(sent=False, detail=f"Unknown job_type={job_type}")

        conn = await self.integrations.get_by_provider(user_id, "telegram")
        jid = job_id_for(user_id, job_type)
        prefs = parse_preferences(conn.config_json if conn else None)

        if conn is None or not conn.enabled:
            await self.runs.start_run(
                user_id=user_id,
                job_type=job_type,
                job_id=jid,
                connection_id=conn.id if conn else None,
                status="skipped",
                skip_reason="telegram_disabled",
            )
            return DigestResponse(sent=False, detail="Telegram not configured or disabled", sections={})

        if not _pref_enabled(prefs, job_type):
            await self.runs.start_run(
                user_id=user_id,
                job_type=job_type,
                job_id=jid,
                connection_id=conn.id,
                status="skipped",
                skip_reason="prefs_off",
            )
            return DigestResponse(sent=False, detail=f"{job_type} disabled in preferences", sections={})

        run = await self.runs.start_run(
            user_id=user_id,
            job_type=job_type,
            job_id=jid,
            connection_id=conn.id,
        )

        tz = _safe_zone(prefs.timezone)
        try:
            built = await BUILDERS[job_type](self.db, user_id, tz)
        except Exception as exc:
            logger.exception("Report build failed user=%s job=%s", user_id, job_type)
            await self.runs.finish_run(run, status="failed", error=str(exc))
            return DigestResponse(sent=False, detail=str(exc), sections={})

        if built.is_empty and job_type in SKIP_IF_EMPTY:
            await self.runs.finish_run(
                run, status="skipped", skip_reason="empty", sections=built.sections, message_chars=0
            )
            return DigestResponse(sent=False, detail="Empty — skipped", sections=built.sections)

        notifier = await build_user_notifier(self.db, user_id, provider="telegram")
        if notifier is None:
            await self.runs.finish_run(
                run, status="skipped", skip_reason="telegram_disabled", sections=built.sections
            )
            return DigestResponse(sent=False, detail="Telegram not configured or disabled", sections=built.sections)

        chunks = tpl.chunk_text(built.text)
        total_chars = 0
        last_detail = ""
        for chunk in chunks:
            result = await notifier.send(NotifierMessage(text=chunk, parse_mode="HTML"))
            total_chars += len(chunk)
            last_detail = result.detail
            if not result.ok:
                await self.runs.finish_run(
                    run,
                    status="failed",
                    error=result.detail,
                    sections=built.sections,
                    message_chars=total_chars,
                )
                return DigestResponse(sent=False, detail=result.detail, sections=built.sections)

        if job_type == "morning":
            conn.last_digest_at = datetime.now(timezone.utc)
            await self.db.flush()

        await self.runs.finish_run(
            run, status="sent", sections=built.sections, message_chars=total_chars
        )
        return DigestResponse(sent=True, detail=last_detail or "ok", sections=built.sections)
