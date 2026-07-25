"""APScheduler wiring for per-user scheduled reports, reminder poller, and outbox drain.

Per-user cron jobs use the user's timezone from TelegramPreferences.
Report entry point is ScheduledReportService.run (same as the manual endpoints).
"""

from __future__ import annotations

import asyncio
import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.database import async_session_factory
from app.modules.integrations.telegram_config import TelegramPreferences, parse_preferences

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_nudge_pending = False

CRON_JOB_TYPES = ("morning", "midday", "night", "weekly", "ai_briefing")


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler


def _job_id(user_id: str, job_type: str = "morning") -> str:
    return f"telegram_{job_type}_{user_id}"


def _safe_zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name or "Asia/Kolkata")
    except ZoneInfoNotFoundError:
        logger.warning("Unknown timezone %s — falling back to Asia/Kolkata", tz_name)
        return ZoneInfo("Asia/Kolkata")


def _time_parts(time_s: str) -> tuple[int, int]:
    hour_s, minute_s = time_s.split(":")
    return int(hour_s), int(minute_s)


def _cron_for_job(job_type: str, prefs: TelegramPreferences) -> CronTrigger | None:
    tz = _safe_zone(prefs.timezone)
    if job_type == "morning":
        if not prefs.morning_enabled:
            return None
        h, m = _time_parts(prefs.morning_time)
        return CronTrigger(hour=h, minute=m, timezone=tz)
    if job_type == "midday":
        if not prefs.midday_enabled:
            return None
        h, m = _time_parts(prefs.midday_time)
        return CronTrigger(hour=h, minute=m, timezone=tz)
    if job_type == "night":
        if not prefs.night_enabled:
            return None
        h, m = _time_parts(prefs.night_time)
        return CronTrigger(hour=h, minute=m, timezone=tz)
    if job_type == "weekly":
        if not prefs.weekly_enabled:
            return None
        h, m = _time_parts(prefs.weekly_time)
        return CronTrigger(day_of_week=str(prefs.weekly_weekday), hour=h, minute=m, timezone=tz)
    if job_type == "ai_briefing":
        if not prefs.ai_briefing_enabled:
            return None
        h, m = _time_parts(prefs.ai_briefing_time)
        return CronTrigger(hour=h, minute=m, timezone=tz)
    return None


def _cron_for_prefs(prefs: TelegramPreferences) -> CronTrigger:
    """Backward-compatible helper used by older Phase 2 tests (legacy digest cron)."""
    hour_s, minute_s = prefs.digest_time.split(":")
    hour, minute = int(hour_s), int(minute_s)
    tz = _safe_zone(prefs.timezone)
    if prefs.digest_frequency == "weekdays":
        return CronTrigger(day_of_week="mon-fri", hour=hour, minute=minute, timezone=tz)
    if prefs.digest_frequency == "weekly":
        return CronTrigger(
            day_of_week=str(prefs.digest_weekday),
            hour=hour,
            minute=minute,
            timezone=tz,
        )
    return CronTrigger(hour=hour, minute=minute, timezone=tz)

async def _run_user_report(user_id: str, job_type: str) -> None:
    from app.modules.integrations.scheduled_report_service import ScheduledReportService

    async with async_session_factory() as session:
        try:
            result = await ScheduledReportService(session).run(user_id, job_type)
            await session.commit()
            logger.info(
                "Scheduled %s for user=%s sent=%s", job_type, user_id, result.sent
            )
        except Exception:
            await session.rollback()
            logger.exception("Scheduled %s failed for user=%s", job_type, user_id)


async def _run_user_digest(user_id: str) -> None:
    """Backward-compatible alias used by older job ids."""
    await _run_user_report(user_id, "morning")


async def _run_reminder_poll() -> None:
    from app.modules.integrations.reminder_scanner import ReminderScanner
    from app.modules.integrations.repository import IntegrationRepository

    async with async_session_factory() as session:
        try:
            conns = await IntegrationRepository(session).list_enabled_telegram()
            scanner = ReminderScanner(session)
            for conn in conns:
                await scanner.scan_user(conn.user_id, connection_id=conn.id)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Reminder poll failed")


async def _run_outbox_drain() -> None:
    from app.modules.integrations.dispatcher import dispatch_pending_notifications

    await dispatch_pending_notifications(limit=50)


def sync_user_jobs(
    user_id: str,
    prefs: TelegramPreferences,
    *,
    enabled: bool,
) -> None:
    """Register or remove all per-user report crons based on prefs."""
    sched = _scheduler
    if sched is None:
        return

    # Remove legacy single digest job id if present
    legacy = f"telegram_digest_{user_id}"
    if sched.get_job(legacy):
        sched.remove_job(legacy)

    for job_type in CRON_JOB_TYPES:
        jid = _job_id(user_id, job_type)
        if sched.get_job(jid):
            sched.remove_job(jid)
        if not enabled:
            continue
        trigger = _cron_for_job(job_type, prefs)
        if trigger is None:
            continue
        sched.add_job(
            _run_user_report,
            trigger=trigger,
            id=jid,
            args=[user_id, job_type],
            replace_existing=True,
            misfire_grace_time=3600,
        )
        logger.info("Registered job %s (%s)", jid, prefs.timezone)


def sync_user_digest_job(
    user_id: str,
    prefs: TelegramPreferences,
    *,
    enabled: bool,
) -> None:
    """Alias for callers that still pass digest prefs."""
    sync_user_jobs(user_id, prefs, enabled=enabled)


def remove_user_digest_job(user_id: str) -> None:
    sched = _scheduler
    if sched is None:
        return
    legacy = f"telegram_digest_{user_id}"
    if sched.get_job(legacy):
        sched.remove_job(legacy)
    for job_type in CRON_JOB_TYPES:
        jid = _job_id(user_id, job_type)
        if sched.get_job(jid):
            sched.remove_job(jid)


async def load_all_scheduled_jobs() -> None:
    """On startup: register report jobs for all enabled Telegram connections."""
    from app.modules.integrations.repository import IntegrationRepository

    async with async_session_factory() as session:
        conns = await IntegrationRepository(session).list_enabled_telegram()
        for conn in conns:
            prefs = parse_preferences(conn.config_json)
            sync_user_jobs(conn.user_id, prefs, enabled=True)


async def load_all_digest_jobs() -> None:
    """Backward-compatible alias."""
    await load_all_scheduled_jobs()


def _schedule_nudge() -> None:
    """Fire a near-real-time outbox drain after the next commit (debounced)."""
    global _nudge_pending
    if _nudge_pending:
        return
    _nudge_pending = True

    async def _nudge() -> None:
        global _nudge_pending
        _nudge_pending = False
        try:
            await _run_outbox_drain()
        except Exception:
            logger.exception("after_commit outbox nudge failed")

    try:
        loop = asyncio.get_running_loop()
        loop.call_soon(lambda: asyncio.create_task(_nudge()))
    except RuntimeError:
        _nudge_pending = False


def _on_session_commit(session: Session) -> None:
    if not session.info.pop("outbox_enqueued", False):
        return
    _schedule_nudge()


def _install_after_commit_hook() -> None:
    try:
        event.listen(Session, "after_commit", _on_session_commit)
    except Exception:
        logger.exception("Failed to install after_commit hook")


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _run_outbox_drain,
        trigger=IntervalTrigger(seconds=30),
        id="outbox_drain",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        _run_reminder_poll,
        trigger=IntervalTrigger(minutes=10),
        id="telegram_reminder_poll",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )
    _scheduler.start()
    _install_after_commit_hook()
    logger.info("APScheduler started (outbox 30s, reminders 10m)")
    return _scheduler


async def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("APScheduler stopped")
