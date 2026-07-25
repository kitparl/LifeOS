"""Telegram webhook handling: authenticate by path secret + chat_id, route updates."""

from __future__ import annotations

import logging
import secrets
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import TelegramWebhookRegisterResponse, TelegramWebhookStatus
from app.modules.integrations.telegram.update_router import route_update
from app.modules.integrations.telegram_client import TelegramClient, TelegramClientError
from app.modules.integrations.telegram_config import parse_config

logger = logging.getLogger(__name__)


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

        if conn.webhook_secret and header_secret is not None and header_secret != conn.webhook_secret:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid secret token")

        cfg = parse_config(conn.config_json)
        if cfg is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Telegram not configured")

        result = await route_update(self.db, conn.user_id, cfg.chat_id, payload)
        if result.get("ok") == "rejected_chat":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Unknown chat")
        return result

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
