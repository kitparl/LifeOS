"""Provider-agnostic notifier abstraction.

Callers send via Notifier; they must not import TelegramClient directly.
Two-way communication can later add a receive()/webhook path behind the same interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.modules.integrations.telegram_client import TelegramClient, TelegramClientError


@dataclass(frozen=True)
class NotifierMessage:
    text: str
    parse_mode: str = "HTML"


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
    """One-way Telegram channel wrapping TelegramClient + chat_id."""

    def __init__(self, client: TelegramClient, chat_id: str):
        self._client = client
        self._chat_id = chat_id

    async def send(self, message: NotifierMessage) -> NotifierResult:
        try:
            await self._client.send_message(
                self._chat_id,
                message.text,
                parse_mode=message.parse_mode,
            )
            return NotifierResult(ok=True, detail="Message sent")
        except TelegramClientError as exc:
            return NotifierResult(ok=False, detail=str(exc) or "Telegram send failed")
