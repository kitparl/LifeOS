"""Thin async adapter for the Telegram Bot HTTP API.

Isolated from domain logic so additional bots/providers can reuse the same pattern.
Never logs bot_token.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class TelegramClientError(Exception):
    """Raised when the Telegram Bot API returns an error or the request fails."""

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _redact_token(token: str, text: str) -> str:
    if not token:
        return text
    return text.replace(token, "***")


class TelegramClient:
    """Minimal Telegram Bot API client (sendMessage, getMe, getUpdates)."""

    def __init__(
        self,
        bot_token: str,
        *,
        base_url: str = "https://api.telegram.org",
        timeout: float = 10.0,
    ):
        if not bot_token or not bot_token.strip():
            raise TelegramClientError("Bot token is required")
        self._token = bot_token.strip()
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    def _method_url(self, method: str) -> str:
        return f"{self._base}/bot{self._token}/{method}"

    async def _post(self, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self._method_url(method)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload or {})
        except httpx.TimeoutException as exc:
            logger.warning("Telegram API timeout on %s", method)
            raise TelegramClientError("Telegram API request timed out") from exc
        except httpx.HTTPError as exc:
            logger.warning("Telegram API transport error on %s: %s", method, type(exc).__name__)
            raise TelegramClientError("Telegram API request failed") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise TelegramClientError(
                "Invalid JSON from Telegram API",
                status_code=response.status_code,
            ) from exc

        if response.status_code >= 400 or not data.get("ok"):
            description = data.get("description") if isinstance(data, dict) else None
            safe = _redact_token(self._token, str(description or "Telegram API error"))
            logger.warning("Telegram API %s failed: %s", method, safe)
            raise TelegramClientError(safe, status_code=response.status_code)

        result = data.get("result")
        if method == "getUpdates":
            return {"result": result if isinstance(result, list) else []}
        if not isinstance(result, dict):
            raise TelegramClientError("Unexpected Telegram API response shape")
        return result

    async def send_message(
        self,
        chat_id: str,
        text: str,
        *,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        return await self._post("sendMessage", payload)

    async def get_me(self) -> dict[str, Any]:
        return await self._post("getMe")

    async def get_updates(self, *, limit: int = 20, timeout: int = 0) -> list[dict[str, Any]]:
        data = await self._post("getUpdates", {"limit": limit, "timeout": timeout})
        result = data.get("result", [])
        return result if isinstance(result, list) else []
