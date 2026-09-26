"""Telegram connection config: bot token/chat id, report preferences, test message, chat-id detection."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, get_or_404
from app.core.timezone import utc_now
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    ChatCandidate,
    DetectChatIdResponse,
    IntegrationUpdate,
    TelegramConfigStatus,
    TelegramConfigUpdate,
    TelegramTestResponse,
)
from app.modules.integrations.telegram.client import TelegramClient, TelegramClientError
from app.modules.integrations.telegram.config import mask_config as mask_telegram_config
from app.modules.integrations.telegram.config import parse_config as parse_telegram_config
from app.modules.integrations.telegram.config import parse_preferences
from app.modules.integrations.telegram.config import serialize_config as serialize_telegram_config
from app.modules.integrations.telegram.templates import test_connection_message

logger = logging.getLogger(__name__)


class TelegramConfigService:
    def __init__(self, db: AsyncSession):
        self.repo = IntegrationRepository(db)

    async def get_or_create_telegram(self, user_id: str):
        return await self.repo.get_or_create(user_id, "telegram", "Telegram")

    async def get_telegram_status(
        self, user_id: str, *, scheduler_warning: str | None = None
    ) -> TelegramConfigStatus:
        conn = await self.get_or_create_telegram(user_id)
        masked = mask_telegram_config(conn.config_json)
        prefs = parse_preferences(conn.config_json)
        webhook_secret = getattr(conn, "webhook_secret", None)

        try:
            from app.modules.integrations.scheduling.scheduler import next_run_times

            next_runs = next_run_times(user_id) if conn.enabled else {}
        except Exception:
            logger.exception("Failed to read scheduler state for user=%s", user_id)
            next_runs = {}

        return TelegramConfigStatus(
            connection_id=conn.id,
            enabled=conn.enabled,
            status=conn.status,
            configured=masked.configured,
            bot_token_masked=masked.bot_token_masked,
            chat_id=masked.chat_id,
            last_sync_at=conn.last_sync_at,
            last_digest_at=getattr(conn, "last_digest_at", None),
            notify_on=prefs.notify_on,
            digest_enabled=prefs.digest_enabled,
            digest_time=prefs.digest_time,
            digest_frequency=prefs.digest_frequency,
            digest_weekday=prefs.digest_weekday,
            timezone=prefs.timezone,
            morning_enabled=prefs.morning_enabled,
            morning_time=prefs.morning_time,
            midday_enabled=prefs.midday_enabled,
            midday_time=prefs.midday_time,
            night_enabled=prefs.night_enabled,
            night_time=prefs.night_time,
            weekly_enabled=prefs.weekly_enabled,
            weekly_time=prefs.weekly_time,
            weekly_weekday=prefs.weekly_weekday,
            ai_briefing_enabled=prefs.ai_briefing_enabled,
            ai_briefing_time=prefs.ai_briefing_time,
            birthday_reminders_enabled=prefs.birthday_reminders_enabled,
            immutable_reminders_enabled=prefs.immutable_reminders_enabled,
            routine_reminders_enabled=prefs.routine_reminders_enabled,
            webhook_configured=bool(webhook_secret),
            webhook_url=None,
            next_runs=next_runs,
            scheduler_warning=scheduler_warning,
        )

    async def save_telegram_config(self, user_id: str, data: TelegramConfigUpdate) -> TelegramConfigStatus:
        conn = await self.get_or_create_telegram(user_id)
        has_secret = data.bot_token is not None or data.chat_id is not None
        has_prefs = any(
            v is not None
            for v in (
                data.notify_on,
                data.digest_enabled,
                data.digest_time,
                data.digest_frequency,
                data.digest_weekday,
                data.timezone,
                data.morning_enabled,
                data.morning_time,
                data.midday_enabled,
                data.midday_time,
                data.night_enabled,
                data.night_time,
                data.weekly_enabled,
                data.weekly_time,
                data.weekly_weekday,
                data.ai_briefing_enabled,
                data.ai_briefing_time,
                data.birthday_reminders_enabled,
                data.immutable_reminders_enabled,
                data.routine_reminders_enabled,
            )
        )
        if data.enabled is None and not has_secret and not has_prefs:
            raise BadRequestError("No fields to update")

        new_json = serialize_telegram_config(
            bot_token=data.bot_token,
            chat_id=data.chat_id,
            existing_json=conn.config_json,
            notify_on=data.notify_on,
            digest_enabled=data.digest_enabled,
            digest_time=data.digest_time,
            digest_frequency=data.digest_frequency,
            digest_weekday=data.digest_weekday,
            timezone=data.timezone,
            morning_enabled=data.morning_enabled,
            morning_time=data.morning_time,
            midday_enabled=data.midday_enabled,
            midday_time=data.midday_time,
            night_enabled=data.night_enabled,
            night_time=data.night_time,
            weekly_enabled=data.weekly_enabled,
            weekly_time=data.weekly_time,
            weekly_weekday=data.weekly_weekday,
            ai_briefing_enabled=data.ai_briefing_enabled,
            ai_briefing_time=data.ai_briefing_time,
            birthday_reminders_enabled=data.birthday_reminders_enabled,
            immutable_reminders_enabled=data.immutable_reminders_enabled,
            routine_reminders_enabled=data.routine_reminders_enabled,
        )

        update = IntegrationUpdate(config_json=new_json)
        if data.enabled is not None:
            update.enabled = data.enabled
        elif parse_telegram_config(new_json) is not None:
            # Auto-enable when credentials become complete unless explicitly disabled
            update.enabled = True

        updated = await self.repo.update(conn, update)
        if parse_telegram_config(updated.config_json) is not None and updated.enabled:
            updated.status = "connected"
            await self.repo.db.flush()

        # Keep per-user scheduled report crons in sync with preferences. A failure
        # here leaves the saved times unscheduled, so it is surfaced to the caller
        # rather than only written to the log.
        scheduler_warning: str | None = None
        try:
            from app.modules.integrations.scheduling.scheduler import get_scheduler, sync_user_jobs

            if get_scheduler() is None:
                scheduler_warning = (
                    "Settings saved, but the scheduler is not running — "
                    "scheduled reports will only start after the API restarts."
                )
            else:
                sync_user_jobs(
                    user_id, parse_preferences(updated.config_json), enabled=updated.enabled
                )
        except Exception:
            logger.exception("Failed to sync scheduled jobs for user=%s", user_id)
            scheduler_warning = (
                "Settings saved, but scheduling them failed. "
                "Check server logs for details."
            )

        return await self.get_telegram_status(user_id, scheduler_warning=scheduler_warning)

    async def test_connection(self, user_id: str, conn_id: str) -> TelegramTestResponse:
        conn = get_or_404(await self.repo.get_by_id(user_id, conn_id), "Integration not found")
        if conn.provider != "telegram":
            raise BadRequestError("Test is only supported for Telegram")

        cfg = parse_telegram_config(conn.config_json)
        if cfg is None:
            return TelegramTestResponse(ok=False, detail="Telegram not configured")

        client = TelegramClient(cfg.bot_token)
        try:
            me = await client.get_me()
            username = me.get("username")
            await client.send_message(
                cfg.chat_id,
                test_connection_message(),
                parse_mode="HTML",
            )
            now = utc_now()
            conn.last_sync_at = now
            conn.status = "connected"
            await self.repo.db.flush()
            return TelegramTestResponse(
                ok=True,
                detail="Test message sent",
                bot_username=str(username) if username else None,
            )
        except TelegramClientError as exc:
            conn.status = "error"
            await self.repo.db.flush()
            logger.warning("Telegram test failed: %s", exc)
            return TelegramTestResponse(ok=False, detail="Telegram test failed")

    async def detect_chat_id(
        self,
        user_id: str,
        conn_id: str,
        bot_token_override: str | None = None,
    ) -> DetectChatIdResponse:
        conn = get_or_404(await self.repo.get_by_id(user_id, conn_id), "Integration not found")
        if conn.provider != "telegram":
            raise BadRequestError("Detect chat id is only for Telegram")

        token = (bot_token_override or "").strip()
        if not token:
            cfg = parse_telegram_config(conn.config_json)
            if cfg is None:
                return DetectChatIdResponse(
                    candidates=[],
                    detail="Provide a bot token or save one first, then message the bot.",
                )
            token = cfg.bot_token

        client = TelegramClient(token)
        try:
            updates = await client.get_updates(limit=50)
        except TelegramClientError:
            return DetectChatIdResponse(candidates=[], detail="Failed to fetch updates")

        seen: dict[str, ChatCandidate] = {}
        for update in updates:
            message = update.get("message") or update.get("channel_post") or {}
            chat = message.get("chat") if isinstance(message, dict) else None
            if not isinstance(chat, dict) or chat.get("id") is None:
                continue
            chat_id = str(chat["id"])
            if chat_id in seen:
                continue
            title = chat.get("title") or " ".join(
                p for p in [chat.get("first_name"), chat.get("last_name")] if p
            ) or None
            seen[chat_id] = ChatCandidate(
                chat_id=chat_id,
                type=chat.get("type"),
                title=title,
                username=chat.get("username"),
            )

        candidates = list(seen.values())
        if not candidates:
            return DetectChatIdResponse(
                candidates=[],
                detail="No chats found. Open your bot in Telegram, press Start (or send a message), then try again.",
            )
        return DetectChatIdResponse(
            candidates=candidates,
            detail=f"Found {len(candidates)} chat(s).",
        )
