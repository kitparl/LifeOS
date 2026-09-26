"""Google Calendar ⇄ LifeOS Calendar sync.

Import (both modes): Google → LifeOS via ``CalendarSyncService`` keyed on
``(source_module="google_calendar", source_id=<Google event id>)``.

Write-back (``sync_direction="two_way"`` only, and only with a read/write grant):
edits/deletes of *Google-linked* LifeOS events are pushed to Google from
``CalendarService``. LifeOS-native events are never pushed — creating events on
the user's Google Calendar from every local entry is too invasive for an MVP.

Loop safety: imports write at the repository level (``CalendarSyncService``) and
never go through ``CalendarService``, so an import can never trigger a push. A
push only happens inside a user-initiated ``CalendarService`` edit; the next
import simply re-reads the same values (idempotent). Conflicts: last write wins.
"""

from __future__ import annotations

import logging
import time as _time
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadGatewayError,
    BadRequestError,
    ServiceUnavailableError,
    TooManyRequestsError,
)
from app.core.timezone import as_utc, utc_now
from app.modules.calendar.models import CalendarEvent
from app.modules.calendar.sync_service import CalendarSyncService
from app.modules.integrations.google_calendar import oauth
from app.modules.integrations.google_calendar.client import GoogleCalendarClient, GoogleCalendarClientError
from app.modules.integrations.google_calendar.config import (
    GoogleCalendarConfig,
    parse_config,
    serialize_config,
)
from app.modules.integrations.google_calendar.mapping import map_google_event, to_google_patch
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    GoogleCalendarConfigStatus,
    GoogleCalendarConfigUpdate,
    IntegrationSyncResponse,
    IntegrationUpdate,
)

logger = logging.getLogger(__name__)

PROVIDER = "google_calendar"
SOURCE_MODULE = "google_calendar"
WINDOW_PAST = timedelta(days=30)
WINDOW_FUTURE = timedelta(days=90)
MANUAL_SYNC_COOLDOWN_SECONDS = 15.0

# user_id -> monotonic time of last manual sync (per-process throttle against quota abuse)
_last_manual_sync: dict[str, float] = {}


class SyncThrottledError(TooManyRequestsError):
    pass


class GoogleCalendarSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = IntegrationRepository(db)

    # ── connection / status ────────────────────────────────────────────────

    async def get_or_create(self, user_id: str):
        return await self.repo.get_or_create(user_id, PROVIDER, "Google Calendar")

    async def get_status(self, user_id: str) -> GoogleCalendarConfigStatus:
        conn = await self.get_or_create(user_id)
        cfg = parse_config(conn.config_json)
        return GoogleCalendarConfigStatus(
            connection_id=conn.id,
            enabled=conn.enabled,
            status=conn.status,
            configured=cfg.connected,
            server_configured=oauth.is_configured(),
            sync_direction=cfg.sync_direction,
            can_write=cfg.can_write,
            last_sync_at=conn.last_sync_at,
            last_sync_message=cfg.last_sync_message,
            last_sync_ok=cfg.last_sync_ok,
        )

    async def save_config(self, user_id: str, data: GoogleCalendarConfigUpdate) -> GoogleCalendarConfigStatus:
        if data.enabled is None and data.sync_direction is None:
            raise BadRequestError("No fields to update")
        conn = await self.get_or_create(user_id)
        cfg = parse_config(conn.config_json)
        if data.enabled and not cfg.connected:
            raise BadRequestError("Connect Google Calendar before enabling sync")
        update = IntegrationUpdate(
            config_json=serialize_config(conn.config_json, sync_direction=data.sync_direction)
        )
        if data.enabled is not None:
            update.enabled = data.enabled
        await self.repo.update(conn, update)
        return await self.get_status(user_id)

    # ── OAuth ──────────────────────────────────────────────────────────────

    def oauth_start(self, user_id: str, direction: str) -> str:
        if not oauth.is_configured():
            raise ServiceUnavailableError(
                "Google Calendar is not configured on the server "
                "(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_CALENDAR_REDIRECT_URI)."
            )
        return oauth.build_auth_url(user_id, direction)

    async def oauth_callback(self, user_id: str, code: str, state: str) -> GoogleCalendarConfigStatus:
        try:
            direction = oauth.verify_state(state, user_id)
        except oauth.GoogleOAuthError as exc:
            logger.warning("Google Calendar OAuth state rejected for user=%s: %s", user_id, exc)
            raise BadRequestError("Google Calendar authorization expired or is invalid. Try connecting again.") from exc
        try:
            refresh_token, scope = await oauth.exchange_code(code)
        except oauth.GoogleOAuthError as exc:
            logger.warning("Google Calendar code exchange failed for user=%s: %s", user_id, exc)
            raise BadGatewayError("Could not complete Google authorization. Try connecting again.") from exc

        conn = await self.get_or_create(user_id)
        old = parse_config(conn.config_json)
        await self.repo.update(
            conn,
            IntegrationUpdate(
                enabled=True,
                config_json=serialize_config(
                    conn.config_json,
                    refresh_token=refresh_token,
                    scope=scope,
                    sync_direction=direction,
                    last_sync_message=None,
                    last_sync_ok=None,
                ),
            ),
        )
        # Replaced grant: revoke the previous refresh token (best effort).
        if old.connected and old.refresh_token != refresh_token:
            await oauth.revoke(old.refresh_token)
        # First import right away; its outcome is reflected in the status message.
        await self.sync(user_id, manual=False)
        return await self.get_status(user_id)

    async def disconnect(self, user_id: str) -> None:
        """Revoke (best effort), delete all Google-sourced events, remove the connection."""
        conn = await self.repo.get_by_provider(user_id, PROVIDER)
        if conn is None:
            return
        cfg = parse_config(conn.config_json)
        await oauth.revoke(cfg.refresh_token)
        result = await self.db.execute(
            select(CalendarEvent).where(
                CalendarEvent.user_id == user_id, CalendarEvent.source_module == SOURCE_MODULE
            )
        )
        for event in result.scalars().all():
            await self.db.delete(event)
        await self.repo.delete(conn)
        await self.db.flush()
        _last_manual_sync.pop(user_id, None)

    # ── import ─────────────────────────────────────────────────────────────

    async def sync(self, user_id: str, *, manual: bool = True) -> IntegrationSyncResponse:
        conn = await self.repo.get_by_provider(user_id, PROVIDER)
        if conn is None or not conn.enabled:
            raise BadRequestError("Google Calendar is not connected or is disabled")
        cfg = parse_config(conn.config_json)
        if not cfg.connected:
            raise BadRequestError("Google Calendar is not connected")

        if manual:
            now_mono = _time.monotonic()
            last = _last_manual_sync.get(user_id)
            if last is not None and now_mono - last < MANUAL_SYNC_COOLDOWN_SECONDS:
                raise SyncThrottledError("Sync just ran. Try again in a few seconds.")
            _last_manual_sync[user_id] = now_mono

        now = utc_now()
        time_min, time_max = now - WINDOW_PAST, now + WINDOW_FUTURE

        # Phase 1 — fetch everything. No local writes until the listing is complete,
        # so a Google/network failure can never delete or half-update local data.
        try:
            access = await oauth.refresh_access_token(cfg.refresh_token)
            items, cal_tz = await GoogleCalendarClient(access, cfg.calendar_id).list_events(time_min, time_max)
        except (oauth.GoogleOAuthError, GoogleCalendarClientError) as exc:
            logger.warning("Google Calendar fetch failed for user=%s: %s", user_id, exc)
            msg = (
                "Google access was revoked or expired. Reconnect Google Calendar."
                if isinstance(exc, oauth.GoogleOAuthError) and "invalid_grant" in str(exc)
                else "Could not reach Google Calendar. Try again later."
            )
            return await self._record(conn, ok=False, message=msg, at=now)

        # Phase 2 — apply atomically (savepoint): all or nothing.
        try:
            async with self.db.begin_nested():
                created, updated, removed, skipped = await self._apply(user_id, items, cal_tz, time_min, time_max)
        except Exception:
            logger.exception("Google Calendar apply failed for user=%s", user_id)
            return await self._record(conn, ok=False, message="Sync failed while saving events.", at=now)

        msg = f"Imported {created} new, updated {updated}, removed {removed}."
        if skipped:
            msg += f" Skipped {skipped} unsupported."
        return await self._record(conn, ok=True, message=msg, at=now, time_zone=cal_tz)

    async def _apply(
        self, user_id: str, items: list[dict], cal_tz: str | None, time_min: datetime, time_max: datetime
    ) -> tuple[int, int, int, int]:
        existing_ids = set(
            (
                await self.db.execute(
                    select(CalendarEvent.source_id).where(
                        CalendarEvent.user_id == user_id, CalendarEvent.source_module == SOURCE_MODULE
                    )
                )
            ).scalars().all()
        )
        sync = CalendarSyncService(self.db)
        seen: set[str] = set()
        created = updated = skipped = 0
        for item in items:
            mapped = map_google_event(item, cal_tz)
            if mapped is None:
                skipped += 1
                continue
            if mapped.source_id in seen:
                continue
            seen.add(mapped.source_id)
            await sync.upsert_from_source(
                user_id=user_id,
                source_module=SOURCE_MODULE,
                source_id=mapped.source_id,
                title=mapped.title,
                starts_at=mapped.starts_at,
                ends_at=mapped.ends_at,
                all_day=mapped.all_day,
                location=mapped.location,
                # "" (not None) so a description removed on Google is cleared locally too.
                description=mapped.description or "",
            )
            if mapped.source_id in existing_ids:
                updated += 1
            else:
                created += 1

        # Vanished from Google inside the window → remove the local copy.
        # Only google_calendar-sourced rows are ever considered.
        stale = (
            await self.db.execute(
                select(CalendarEvent.source_id).where(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.source_module == SOURCE_MODULE,
                    CalendarEvent.starts_at >= time_min,
                    CalendarEvent.starts_at <= time_max,
                )
            )
        ).scalars().all()
        removed = 0
        for source_id in stale:
            if source_id and source_id not in seen:
                await sync.delete_from_source(user_id, SOURCE_MODULE, source_id)
                removed += 1
        return created, updated, removed, skipped

    async def _record(
        self, conn, *, ok: bool, message: str, at: datetime, time_zone: str | None = None
    ) -> IntegrationSyncResponse:
        conn.config_json = serialize_config(
            conn.config_json, last_sync_message=message, last_sync_ok=ok, time_zone=time_zone
        )
        conn.status = "synced" if ok else "error"
        if ok:
            conn.last_sync_at = at
        await self.db.flush()
        return IntegrationSyncResponse(
            provider=PROVIDER, status="synced" if ok else "error", message=message, synced_at=at
        )

    # ── write-back (two-way) + read-only guard ─────────────────────────────

    async def _write_back_config(self, user_id: str) -> GoogleCalendarConfig | None:
        """Config if two-way write-back is active for this user, else None."""
        conn = await self.repo.get_by_provider(user_id, PROVIDER)
        if conn is None or not conn.enabled:
            return None
        cfg = parse_config(conn.config_json)
        if cfg.connected and cfg.sync_direction == "two_way" and cfg.can_write:
            return cfg
        return None

    async def is_read_only(self, user_id: str) -> bool:
        """Google-sourced events are read-only unless two-way write-back is active."""
        return await self._write_back_config(user_id) is None

    async def _client(self, cfg: GoogleCalendarConfig) -> GoogleCalendarClient:
        access = await oauth.refresh_access_token(cfg.refresh_token)
        return GoogleCalendarClient(access, cfg.calendar_id)

    async def push_update(self, user_id: str, event: CalendarEvent, changes: dict) -> None:
        """Called by CalendarService BEFORE applying a local edit to a Google-linked event.

        Raises (and so aborts the local edit) when read-only or when Google rejects it.
        """
        cfg = await self._write_back_config(user_id)
        if cfg is None:
            raise BadRequestError(
                "Synced from Google Calendar (read-only). Enable two-way sync to edit."
            )
        if ("recurrence" in changes and changes["recurrence"] not in (None, "none")) or (
            "event_kind" in changes and changes["event_kind"] not in (None, "normal")
        ):
            raise BadRequestError("Recurrence and event type of Google Calendar events are managed in Google.")

        def pick(key: str):
            return changes[key] if key in changes else getattr(event, key)

        body = to_google_patch(
            title=pick("title"),
            description=pick("description"),
            location=pick("location"),
            starts_at=as_utc(pick("starts_at")),
            ends_at=as_utc(pick("ends_at")) if pick("ends_at") else None,
            all_day=bool(pick("all_day")),
            calendar_tz=cfg.time_zone,
        )
        try:
            await (await self._client(cfg)).patch_event(event.source_id, body)
        except (oauth.GoogleOAuthError, GoogleCalendarClientError) as exc:
            logger.warning("Google Calendar push update failed for user=%s: %s", user_id, exc)
            raise BadGatewayError("Could not update Google Calendar; try again.") from exc

    async def push_delete(self, user_id: str, event: CalendarEvent) -> None:
        """Called by CalendarService BEFORE deleting a Google-linked event locally."""
        cfg = await self._write_back_config(user_id)
        if cfg is None:
            raise BadRequestError(
                "Synced from Google Calendar (read-only). Enable two-way sync to delete."
            )
        try:
            await (await self._client(cfg)).delete_event(event.source_id)
        except (oauth.GoogleOAuthError, GoogleCalendarClientError) as exc:
            logger.warning("Google Calendar push delete failed for user=%s: %s", user_id, exc)
            raise BadGatewayError("Could not delete from Google Calendar; try again.") from exc


async def sync_all_enabled() -> None:
    """Scheduler entry point: import for every enabled connection, one session per user."""
    from app.core.database import async_session_factory

    async with async_session_factory() as session:
        conns = await IntegrationRepository(session).list_enabled_by_provider(PROVIDER)
        user_ids = [c.user_id for c in conns]
    for user_id in user_ids:
        async with async_session_factory() as session:
            try:
                await GoogleCalendarSyncService(session).sync(user_id, manual=False)
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception("Scheduled Google Calendar sync failed for user=%s", user_id)
