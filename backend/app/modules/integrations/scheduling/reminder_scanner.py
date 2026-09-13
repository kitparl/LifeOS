"""Scan upcoming birthdays, immutable events, and routine blocks for reminder ladders.

Runs every 10 minutes via the shared APScheduler job `telegram_reminder_poll`.
Idempotent: one send per (user + occurrence + offset) via unique dedupe_key.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.repository import CalendarRepository
from app.modules.calendar.service import _expand_recurring_event
from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.notifier import NotifierMessage
from app.modules.integrations.notifier_registry import build_user_notifier
from app.modules.integrations.report_repository import ReportRunRepository
from app.modules.integrations.telegram_config import parse_preferences
from app.modules.routines.service import RoutineService

logger = logging.getLogger(__name__)

# Birthday offsets relative to birthday local date
BIRTHDAY_DAY_OFFSETS = (2, 1)  # T-2, T-1 (day-of handled separately at 11:55)
BIRTHDAY_DAY_OF_TIME = (11, 55)  # 11:55 local

# Immutable event offsets before start
IMMUTABLE_OFFSETS = (
    ("7d", timedelta(days=7)),
    ("3d", timedelta(days=3)),
    ("1d", timedelta(days=1)),
    ("6h", timedelta(hours=6)),
    ("1h", timedelta(hours=1)),
    ("59m", timedelta(minutes=59)),
)

# Routine lead-times before block start
ROUTINE_OFFSETS = (
    ("30m", timedelta(minutes=30)),
    ("15m", timedelta(minutes=15)),
    ("5m", timedelta(minutes=5)),
    ("1m", timedelta(minutes=1)),
)

# Poller window: match offsets whose fire time falls in [now - grace, now]
POLL_GRACE = timedelta(minutes=10)


def _safe_zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name or "Asia/Kolkata")
    except ZoneInfoNotFoundError:
        return ZoneInfo("Asia/Kolkata")


def _aware(dt: datetime, tz: ZoneInfo) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt


def _in_window(fire_at: datetime, now: datetime) -> bool:
    return now - POLL_GRACE <= fire_at <= now


class ReminderScanner:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.runs = ReportRunRepository(db)

    async def scan_user(self, user_id: str, *, connection_id: str | None = None) -> int:
        """Scan and send due reminders for one user. Returns send count."""
        from app.modules.integrations.repository import IntegrationRepository

        conn = await IntegrationRepository(self.db).get_by_provider(user_id, "telegram")
        if conn is None or not conn.enabled:
            return 0
        prefs = parse_preferences(conn.config_json)
        tz = _safe_zone(prefs.timezone)
        now = datetime.now(tz)
        sent = 0

        if prefs.birthday_reminders_enabled:
            sent += await self._scan_birthdays(user_id, conn.id, tz, now)
        if prefs.immutable_reminders_enabled:
            sent += await self._scan_immutable(user_id, conn.id, tz, now)
        if prefs.routine_reminders_enabled:
            sent += await self._scan_routines(user_id, conn.id, tz, now)
        return sent

    async def _send(
        self,
        *,
        user_id: str,
        connection_id: str,
        job_type: str,
        dedupe_key: str,
        text: str,
        scheduled_for: datetime,
    ) -> bool:
        run = await self.runs.claim_dedupe(
            user_id=user_id,
            job_type=job_type,
            dedupe_key=dedupe_key,
            job_id="telegram_reminder_poll",
            connection_id=connection_id,
            scheduled_for=scheduled_for,
        )
        if run is None:
            return False
        notifier = await build_user_notifier(self.db, user_id, provider="telegram")
        if notifier is None:
            await self.runs.finish_run(run, status="skipped", skip_reason="telegram_disabled")
            return False
        result = await notifier.send(NotifierMessage(text=text, parse_mode="HTML"))
        if result.ok:
            await self.runs.finish_run(run, status="sent", message_chars=len(text))
            return True
        await self.runs.finish_run(run, status="failed", error=result.detail, message_chars=len(text))
        return False

    async def _scan_birthdays(
        self, user_id: str, connection_id: str, tz: ZoneInfo, now: datetime
    ) -> int:
        # Look ahead 3 days for birthday occurrences
        start = now - timedelta(days=1)
        end = now + timedelta(days=3)
        events = await CalendarRepository(self.db).list_events(user_id, start=start, end=end)
        sent = 0
        today = now.date()

        for event in events:
            kind = getattr(event, "event_kind", None) or "normal"
            if kind != "birthday":
                continue
            # Expand yearly occurrences in the window
            occurrences = _expand_recurring_event(event, start, end)
            for occ in occurrences:
                occ_date = occ.starts_at.astimezone(tz).date() if occ.starts_at.tzinfo else occ.starts_at.date()
                master_id = event.id

                # T-2 / T-1: fire around local morning of the offset day (match poller window
                # any time that day once the offset date is "today")
                for days_before in BIRTHDAY_DAY_OFFSETS:
                    target_day = occ_date - timedelta(days=days_before)
                    if target_day != today:
                        continue
                    # Fire at 06:00 local on the reminder day (within poller grace)
                    fire_at = datetime.combine(target_day, datetime.min.time().replace(hour=6), tzinfo=tz)
                    # Also accept any poll during that calendar day if we haven't sent yet —
                    # use start-of-day as scheduled_for and rely on dedupe.
                    if not (target_day == today):
                        continue
                    label = "tomorrow" if days_before == 1 else f"in {days_before} days"
                    key = f"bday:{master_id}:{occ_date.isoformat()}:tminus{days_before}"
                    text = tpl.birthday_reminder(title=event.title, when=f"Birthday {label}")
                    if await self._send(
                        user_id=user_id,
                        connection_id=connection_id,
                        job_type="birthday_reminder",
                        dedupe_key=key,
                        text=text,
                        scheduled_for=fire_at,
                    ):
                        sent += 1

                # Day-of at 11:55 local
                if occ_date == today:
                    fire_at = datetime.combine(
                        occ_date,
                        datetime.min.time().replace(hour=BIRTHDAY_DAY_OF_TIME[0], minute=BIRTHDAY_DAY_OF_TIME[1]),
                        tzinfo=tz,
                    )
                    if _in_window(fire_at, now):
                        key = f"bday:{master_id}:{occ_date.isoformat()}:dayof"
                        text = tpl.birthday_reminder(title=event.title, when="Today")
                        if await self._send(
                            user_id=user_id,
                            connection_id=connection_id,
                            job_type="birthday_reminder",
                            dedupe_key=key,
                            text=text,
                            scheduled_for=fire_at,
                        ):
                            sent += 1
        return sent

    async def _scan_immutable(
        self, user_id: str, connection_id: str, tz: ZoneInfo, now: datetime
    ) -> int:
        start = now - timedelta(hours=1)
        end = now + timedelta(days=8)
        events = await CalendarRepository(self.db).list_events(user_id, start=start, end=end)
        sent = 0
        for event in events:
            kind = getattr(event, "event_kind", None) or "normal"
            if kind != "immutable":
                continue
            if event.recurrence and event.recurrence != "none":
                occurrences = _expand_recurring_event(event, start, end)
            else:
                from app.modules.calendar.schemas import EventListItem

                occurrences = [EventListItem.model_validate(event)]

            for occ in occurrences:
                starts = _aware(occ.starts_at, tz).astimezone(tz)
                master_id = event.id
                occ_iso = starts.isoformat()
                for offset_label, delta in IMMUTABLE_OFFSETS:
                    fire_at = starts - delta
                    if not _in_window(fire_at, now):
                        continue
                    key = f"imm:{master_id}:{occ_iso}:{offset_label}"
                    when = starts.strftime("%Y-%m-%d %H:%M")
                    text = tpl.immutable_reminder(
                        title=event.title, when=when, offset_label=f"{offset_label} before"
                    )
                    if await self._send(
                        user_id=user_id,
                        connection_id=connection_id,
                        job_type="immutable_reminder",
                        dedupe_key=key,
                        text=text,
                        scheduled_for=fire_at,
                    ):
                        sent += 1
        return sent

    async def _scan_routines(
        self, user_id: str, connection_id: str, tz: ZoneInfo, now: datetime
    ) -> int:
        # Expand today + tomorrow so late-night / early blocks are covered
        day_start = datetime.combine(now.date(), datetime.min.time(), tzinfo=tz)
        day_end = day_start + timedelta(days=2)
        items = await RoutineService(self.db).expand_for_calendar(user_id, day_start, day_end)
        sent = 0
        for item in items:
            starts = _aware(item.starts_at, tz).astimezone(tz)
            # id format: routine:{routine_id}:{block_id}:{date}
            parts = item.id.split(":")
            routine_id = parts[1] if len(parts) >= 2 else "x"
            block_start_key = starts.strftime("%H%M")
            occ_date = starts.date().isoformat()
            for offset_label, delta in ROUTINE_OFFSETS:
                fire_at = starts - delta
                if not _in_window(fire_at, now):
                    continue
                key = f"routine:{routine_id}:{block_start_key}:{occ_date}:{offset_label}"
                text = tpl.routine_reminder(
                    title=item.title,
                    starts=starts.strftime("%H:%M"),
                    offset_label=f"in {offset_label}",
                )
                if await self._send(
                    user_id=user_id,
                    connection_id=connection_id,
                    job_type="routine_reminder",
                    dedupe_key=key,
                    text=text,
                    scheduled_for=fire_at,
                ):
                    sent += 1
        return sent
