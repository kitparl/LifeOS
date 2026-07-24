"""APScheduler wiring for per-user digests and outbox drain.

Per-user cron jobs use the user's timezone from TelegramPreferences.
Digest entry point is DigestService.send_digest (same as the manual endpoint).
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


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler


def _job_id(user_id: str) -> str:
    return f"telegram_digest_{user_id}"


def _safe_zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name or "UTC")
    except ZoneInfoNotFoundError:
        logger.warning("Unknown timezone %s — falling back to UTC", tz_name)
        return ZoneInfo("UTC")


def _cron_for_prefs(prefs: TelegramPreferences) -> CronTrigger:
    hour_s, minute_s = prefs.digest_time.split(":")
    hour, minute = int(hour_s), int(minute_s)
    tz = _safe_zone(prefs.timezone)
    if prefs.digest_frequency == "weekdays":
        return CronTrigger(day_of_week="mon-fri", hour=hour, minute=minute, timezone=tz)
    if prefs.digest_frequency == "weekly":
        # APScheduler: 0=Mon … 6=Sun matches our digest_weekday
        return CronTrigger(
            day_of_week=str(prefs.digest_weekday),
            hour=hour,
            minute=minute,
            timezone=tz,
        )
    return CronTrigger(hour=hour, minute=minute, timezone=tz)


async def _run_user_digest(user_id: str) -> None:
    from app.modules.integrations.digest_service import DigestService

    async with async_session_factory() as session:
        try:
            result = await DigestService(session).send_digest(user_id)
            await session.commit()
            logger.info("Scheduled digest for user=%s sent=%s", user_id, result.sent)
        except Exception:
            await session.rollback()
            logger.exception("Scheduled digest failed for user=%s", user_id)


async def _run_outbox_drain() -> None:
    from app.modules.integrations.dispatcher import dispatch_pending_notifications

    await dispatch_pending_notifications(limit=50)


def sync_user_digest_job(
    user_id: str,
    prefs: TelegramPreferences,
    *,
    enabled: bool,
) -> None:
    """Register or remove the per-user digest cron based on prefs."""
    sched = _scheduler
    if sched is None:
        return
    jid = _job_id(user_id)
    if sched.get_job(jid):
        sched.remove_job(jid)
    if not enabled or not prefs.digest_enabled:
        return
    trigger = _cron_for_prefs(prefs)
    sched.add_job(
        _run_user_digest,
        trigger=trigger,
        id=jid,
        args=[user_id],
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Registered digest job %s at %s (%s)", jid, prefs.digest_time, prefs.timezone)


def remove_user_digest_job(user_id: str) -> None:
    sched = _scheduler
    if sched is None:
        return
    jid = _job_id(user_id)
    if sched.get_job(jid):
        sched.remove_job(jid)


async def load_all_digest_jobs() -> None:
    """On startup: register digest jobs for all enabled Telegram connections."""
    from app.modules.integrations.repository import IntegrationRepository

    async with async_session_factory() as session:
        conns = await IntegrationRepository(session).list_enabled_telegram()
        for conn in conns:
            prefs = parse_preferences(conn.config_json)
            sync_user_digest_job(conn.user_id, prefs, enabled=True)


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
    # Only nudge when this transaction enqueued outbox rows (set by subscriber).
    if not session.info.pop("outbox_enqueued", False):
        return
    _schedule_nudge()


def _install_after_commit_hook() -> None:
    # SQLAlchemy async sessions use the sync Session under the hood.
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
    _scheduler.start()
    _install_after_commit_hook()
    logger.info("APScheduler started (outbox drain every 30s)")
    return _scheduler


async def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("APScheduler stopped")
