"""Telegram webhook handling: authenticate by path secret + chat_id, route commands."""

from __future__ import annotations

import logging
import secrets
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.integrations.command_handler import handle_command
from app.modules.integrations.notifier import NotifierMessage
from app.modules.integrations.notifier_registry import build_user_notifier
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import TelegramWebhookRegisterResponse, TelegramWebhookStatus
from app.modules.integrations.telegram_client import TelegramClient, TelegramClientError
from app.modules.integrations.telegram_config import parse_config

logger = logging.getLogger(__name__)


def _extract_message(update: dict[str, Any]) -> dict[str, Any] | None:
    msg = update.get("message") or update.get("edited_message") or update.get("channel_post")
    return msg if isinstance(msg, dict) else None


class TelegramWebhookService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = IntegrationRepository(db)

    async def handle_update(
        self,
        path_secret: str,
        payload: dict[str, Any],
        *,
        header_secret: str | None = None,
    ) -> dict[str, str]:
        conn = await self.repo.get_by_webhook_secret(path_secret)
        if conn is None or not conn.enabled:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown webhook")

        # Optional header check (Telegram secret_token)
        if conn.webhook_secret and header_secret is not None and header_secret != conn.webhook_secret:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid secret token")

        cfg = parse_config(conn.config_json)
        if cfg is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Telegram not configured")

        msg = _extract_message(payload)
        if msg is None:
            return {"ok": "ignored"}

        chat = msg.get("chat") if isinstance(msg.get("chat"), dict) else {}
        chat_id = str(chat.get("id") or "")
        if not chat_id or chat_id != cfg.chat_id:
            logger.warning("Rejected Telegram update from unknown chat_id")
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Unknown chat")

        text = str(msg.get("text") or "").strip()
        if not text:
            return {"ok": "ignored"}

        reply = await handle_command(self.db, conn.user_id, text)
        notifier = await build_user_notifier(self.db, conn.user_id, provider="telegram")
        if notifier is not None:
            await notifier.send(NotifierMessage(text=reply, parse_mode="HTML"))
        return {"ok": "processed"}

    async def register_webhook(self, user_id: str) -> TelegramWebhookRegisterResponse:
        settings = get_settings()
        base = (settings.public_base_url or "").rstrip("/")
        if not base:
            return TelegramWebhookRegisterResponse(
                ok=False,
                detail="PUBLIC_BASE_URL is not configured",
                webhook_url=None,
            )

        conn = await self.repo.get_by_provider(user_id, "telegram")
        if conn is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Telegram not configured")
        cfg = parse_config(conn.config_json)
        if cfg is None:
            return TelegramWebhookRegisterResponse(
                ok=False, detail="Save bot token and chat id first", webhook_url=None
            )

        secret = conn.webhook_secret or secrets.token_urlsafe(24)
        conn.webhook_secret = secret
        await self.db.flush()

        webhook_url = f"{base}/api/v1/integrations/telegram/webhook/{secret}"
        client = TelegramClient(cfg.bot_token)
        try:
            await client.set_webhook(webhook_url, secret_token=secret, drop_pending_updates=False)
        except TelegramClientError as exc:
            return TelegramWebhookRegisterResponse(ok=False, detail=str(exc), webhook_url=webhook_url)
        return TelegramWebhookRegisterResponse(
            ok=True, detail="Webhook registered", webhook_url=webhook_url
        )

    async def delete_webhook(self, user_id: str) -> TelegramWebhookRegisterResponse:
        conn = await self.repo.get_by_provider(user_id, "telegram")
        if conn is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Telegram not configured")
        cfg = parse_config(conn.config_json)
        if cfg is not None:
            try:
                await TelegramClient(cfg.bot_token).delete_webhook(drop_pending_updates=False)
            except TelegramClientError as exc:
                logger.warning("deleteWebhook failed: %s", exc)
        conn.webhook_secret = None
        await self.db.flush()
        return TelegramWebhookRegisterResponse(ok=True, detail="Webhook removed", webhook_url=None)

    async def webhook_status(self, user_id: str) -> TelegramWebhookStatus:
        conn = await self.repo.get_by_provider(user_id, "telegram")
        if conn is None:
            return TelegramWebhookStatus(configured=False, detail="Not configured")
        cfg = parse_config(conn.config_json)
        if cfg is None:
            return TelegramWebhookStatus(
                configured=bool(conn.webhook_secret),
                detail="Credentials incomplete",
            )
        try:
            info = await TelegramClient(cfg.bot_token).get_webhook_info()
        except TelegramClientError as exc:
            return TelegramWebhookStatus(
                configured=bool(conn.webhook_secret),
                detail=str(exc),
            )
        return TelegramWebhookStatus(
            configured=bool(info.get("url")),
            url=info.get("url"),
            pending_update_count=info.get("pending_update_count"),
            last_error_message=info.get("last_error_message"),
            detail="ok",
        )
