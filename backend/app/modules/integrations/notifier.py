"""Provider-agnostic notifier abstraction.

Callers send via Notifier; they must not import TelegramClient directly.
Two-way communication can later add a receive()/webhook path behind the same interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.modules.integrations.telegram_client import TelegramClient, TelegramClientError


@dataclass(frozen=True)
class NotifierMessage:
    text: str
    parse_mode: str = "HTML"
    reply_markup: dict[str, Any] | None = None


@dataclass(frozen=True)
class NotifierResult:
    ok: bool
    detail: str


class Notifier(ABC):
    """Outbound notification channel.

    Future two-way support can add:
      async def receive(...) -> ...
    without changing existing send() callers.
    """

    @abstractmethod
    async def send(self, message: NotifierMessage) -> NotifierResult:
        ...


class TelegramNotifier(Notifier):
    """Telegram channel wrapping TelegramClient + chat_id."""

    def __init__(self, client: TelegramClient, chat_id: str):
        self._client = client
        self._chat_id = chat_id

    @property
    def client(self) -> TelegramClient:
        return self._client

    @property
    def chat_id(self) -> str:
        return self._chat_id

    async def send(self, message: NotifierMessage) -> NotifierResult:
        try:
            await self._client.send_message(
                self._chat_id,
                message.text,
                parse_mode=message.parse_mode,
                reply_markup=message.reply_markup,
            )
            return NotifierResult(ok=True, detail="Message sent")
        except TelegramClientError as exc:
            return NotifierResult(ok=False, detail=str(exc) or "Telegram send failed")

    async def edit_message(
        self,
        message_id: int,
        message: NotifierMessage,
    ) -> NotifierResult:
        try:
            await self._client.edit_message_text(
                self._chat_id,
                message_id,
                message.text,
                parse_mode=message.parse_mode,
                reply_markup=message.reply_markup,
            )
            return NotifierResult(ok=True, detail="Message edited")
        except TelegramClientError as exc:
            return NotifierResult(ok=False, detail=str(exc) or "Telegram edit failed")

    async def answer_callback(
        self,
        callback_query_id: str,
        *,
        text: str = "",
        show_alert: bool = False,
    ) -> NotifierResult:
        try:
            await self._client.answer_callback_query(
                callback_query_id, text=text, show_alert=show_alert
            )
            return NotifierResult(ok=True, detail="Callback answered")
        except TelegramClientError as exc:
            return NotifierResult(ok=False, detail=str(exc) or "Telegram callback failed")
