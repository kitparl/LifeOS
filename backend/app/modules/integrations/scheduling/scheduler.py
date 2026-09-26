"""APScheduler wiring for per-user scheduled reports, reminder poller, and outbox drain.

Per-user cron jobs use the user's timezone from TelegramPreferences.
Report entry point is ScheduledReportService.run (same as the manual endpoints).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from typing import TypeVar

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.database import async_session_factory
from app.core.timezone import IST, safe_zone
from app.modules.integrations.telegram.config import TelegramPreferences, parse_preferences

logger = logging.getLogger(__name__)
T = TypeVar("T")

_scheduler: AsyncIOScheduler | None = None
_nudge_pending = False

CRON_JOB_TYPES = ("morning", "midday", "night", "weekly", "ai_briefing")
# job type -> (enabled flag, "HH:MM" time) attribute names on TelegramPreferences
_JOB_PREF_FIELDS: dict[str, tuple[str, str]] = {
    "morning": ("morning_enabled", "morning_time"),
    "midday": ("midday_enabled", "midday_time"),
    "night": ("night_enabled", "night_time"),
    "weekly": ("weekly_enabled", "weekly_time"),
    "ai_briefing": ("ai_briefing_enabled", "ai_briefing_time"),
}


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler


def job_id_for(user_id: str, job_type: str) -> str:
    return f"telegram_{job_type}_{user_id}"


def job_enabled(prefs: TelegramPreferences, job_type: str) -> bool:
    fields = _JOB_PREF_FIELDS.get(job_type)
    return bool(fields and getattr(prefs, fields[0]))


def _time_parts(time_s: str) -> tuple[int, int]:
    hour_s, minute_s = time_s.split(":")
    return int(hour_s), int(minute_s)


def _cron_for_job(job_type: str, prefs: TelegramPreferences) -> CronTrigger | None:
    tz = safe_zone(prefs.timezone)
    if not job_enabled(prefs, job_type):
        return None
    h, m = _time_parts(getattr(prefs, _JOB_PREF_FIELDS[job_type][1]))
    if job_type == "weekly":
        return CronTrigger(day_of_week=str(prefs.weekly_weekday), hour=h, minute=m, timezone=tz)
    return CronTrigger(hour=h, minute=m, timezone=tz)


async def _run_in_session(label: str, work: Callable[[AsyncSession], Awaitable[T]]) -> T | None:
    """Run one maintenance job in its own session: commit on success, roll back and log on failure."""
    async with async_session_factory() as session:
        try:
            result = await work(session)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            logger.exception("%s job failed", label)
            return None


async def _run_user_report(user_id: str, job_type: str) -> None:
    from app.modules.integrations.scheduling.scheduled_report_service import ScheduledReportService

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


async def _run_reminder_poll() -> None:
    from app.modules.integrations.repository import IntegrationRepository
    from app.modules.integrations.scheduling.reminder_scanner import ReminderScanner

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
    from app.modules.integrations.notifications.dispatcher import dispatch_pending_notifications

    await dispatch_pending_notifications(limit=50)


async def _run_qa_purge() -> None:
    from app.modules.qa.service import QAService

    n = await _run_in_session("Q&A purge", lambda session: QAService(session).purge_expired())
    if n:
        logger.info("Purged %s expired Q&A entries", n)


async def _run_sticky_notes_purge() -> None:
    from app.modules.sticky_notes.service import StickyNoteService

    n = await _run_in_session("Sticky notes purge", lambda session: StickyNoteService(session).purge_expired())
    if n:
        logger.info("Purged %s expired sticky notes", n)


async def _run_news_saved_purge() -> None:
    from app.modules.news.service import NewsService

    n = await _run_in_session("Saved news purge", lambda session: NewsService(session).purge_expired())
    if n:
        logger.info("Purged %s expired saved news articles", n)


async def _run_google_calendar_sync() -> None:
    from app.modules.integrations.google_calendar.sync_service import sync_all_enabled

    try:
        await sync_all_enabled()
    except Exception:
        logger.exception("Google Calendar sync job failed")


async def _run_routines_expire() -> None:
    from app.modules.routines.service import RoutineService

    n = await _run_in_session(
        "Routine expiry", lambda session: RoutineService(session).deactivate_expired(date.today())
    )
    if n is not None:
        logger.info("Expired %s routines", n)


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
        jid = job_id_for(user_id, job_type)
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


def next_run_times(user_id: str) -> dict[str, datetime | None]:
    """Next fire time per cron job type, so clients can verify what is registered."""
    sched = _scheduler
    if sched is None:
        return {}
    runs: dict[str, datetime | None] = {}
    for job_type in CRON_JOB_TYPES:
        job = sched.get_job(job_id_for(user_id, job_type))
        runs[job_type] = getattr(job, "next_run_time", None) if job else None
    return runs


def remove_user_digest_job(user_id: str) -> None:
    sched = _scheduler
    if sched is None:
        return
    legacy = f"telegram_digest_{user_id}"
    if sched.get_job(legacy):
        sched.remove_job(legacy)
    for job_type in CRON_JOB_TYPES:
        jid = job_id_for(user_id, job_type)
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
    _scheduler.add_job(
        _run_routines_expire,
        trigger=CronTrigger(hour=0, minute=1, timezone=IST),
        id="routines_expire",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
    _scheduler.add_job(
        _run_qa_purge,
        trigger=CronTrigger(hour=0, minute=5, timezone=IST),
        id="qa_purge",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
    _scheduler.add_job(
        _run_sticky_notes_purge,
        trigger=CronTrigger(hour=0, minute=6, timezone=IST),
        id="sticky_notes_purge",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
    _scheduler.add_job(
        _run_news_saved_purge,
        trigger=CronTrigger(hour=0, minute=7, timezone=IST),
        id="news_saved_purge",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
    _scheduler.add_job(
        _run_google_calendar_sync,
        trigger=IntervalTrigger(minutes=30),
        id="google_calendar_sync",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=600,
    )
    _scheduler.start()
    _install_after_commit_hook()
    logger.info(
        "APScheduler started (outbox 30s, reminders 10m, routines expire 00:01 IST, "
        "qa purge 00:05 IST, sticky notes purge 00:06 IST, news saved purge 00:07 IST, google calendar 30m)"
    )
    return _scheduler


async def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("APScheduler stopped")
