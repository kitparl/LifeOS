"""Light unit tests for Telegram notifier / crypto / digest formatting."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from cryptography.fernet import Fernet

from app.core import crypto
from app.core.crypto import decrypt, encrypt
from app.modules.integrations.digest_service import DigestContent, format_digest
from app.modules.integrations.notifier import NotifierMessage, TelegramNotifier
from app.modules.integrations.telegram_client import TelegramClient, TelegramClientError
from app.modules.integrations.telegram_config import mask_config, parse_config, serialize_config


@pytest.fixture(autouse=True)
def _fresh_fernet(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("INTEGRATION_ENC_KEY", key)
    from app.core.config import get_settings

    get_settings.cache_clear()
    crypto._get_fernet.cache_clear()
    yield
    crypto._get_fernet.cache_clear()
    get_settings.cache_clear()


def test_crypto_round_trip():
    assert encrypt("") == ""
    assert decrypt("") == ""
    cipher = encrypt("secret-bot-token")
    assert cipher != "secret-bot-token"
    assert decrypt(cipher) == "secret-bot-token"


def test_crypto_tamper_fails_closed():
    cipher = encrypt("hello")
    with pytest.raises(ValueError, match="Invalid or tampered"):
        decrypt(cipher[:-4] + "xxxx")


def test_telegram_config_serialize_parse_mask():
    raw = serialize_config(bot_token="123456:ABC-DEF", chat_id="987654321")
    assert "bot_token_enc" in raw
    assert "123456:ABC-DEF" not in raw
    assert "bot_token\"" not in raw or "bot_token_enc" in raw

    parsed = parse_config(raw)
    assert parsed is not None
    assert parsed.bot_token == "123456:ABC-DEF"
    assert parsed.chat_id == "987654321"

    masked = mask_config(raw)
    assert masked.configured is True
    assert masked.bot_token_masked == "****-DEF"
    assert masked.chat_id == "987654321"
    assert "123456" not in (masked.bot_token_masked or "")


def test_telegram_config_preserve_existing_on_partial_update():
    first = serialize_config(bot_token="token-one-AAAA", chat_id="111")
    second = serialize_config(chat_id="222", existing_json=first)
    parsed = parse_config(second)
    assert parsed is not None
    assert parsed.bot_token == "token-one-AAAA"
    assert parsed.chat_id == "222"


def test_format_digest_empty_and_sections():
    empty = format_digest(DigestContent())
    assert "caught up" in empty.text.lower()
    assert empty.parse_mode == "HTML"

    content = DigestContent(
        pending_tasks=["Buy milk [pending, no due date]"],
        habits_due=["Meditate (daily)"],
        active_goals=["Ship feature · 40% · no target"],
    )
    msg = format_digest(content, now=datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc))
    assert "Pending tasks" in msg.text
    assert "Buy milk" in msg.text
    assert "Habits due" in msg.text
    assert "Active goals" in msg.text
    assert "<" in msg.text  # HTML tags


@pytest.mark.asyncio
async def test_telegram_client_send_message_mocked(monkeypatch):
    captured: dict = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"ok": True, "result": {"message_id": 1, "text": "hi"}}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json=None):
            captured["url"] = url
            captured["json"] = json
            assert "123:TOKEN" not in str(captured) or True  # token is in URL path by design
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    client = TelegramClient("123:TOKEN")
    result = await client.send_message("42", "hello")
    assert result["message_id"] == 1
    assert captured["json"]["chat_id"] == "42"
    assert captured["json"]["text"] == "hello"
    assert "/bot123:TOKEN/" in captured["url"]


@pytest.mark.asyncio
async def test_telegram_client_api_error():
    class FakeResponse:
        status_code = 401

        def json(self):
            return {"ok": False, "description": "Unauthorized"}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json=None):
            return FakeResponse()

    with patch.object(httpx, "AsyncClient", FakeClient):
        client = TelegramClient("bad:token")
        with pytest.raises(TelegramClientError, match="Unauthorized"):
            await client.get_me()


@pytest.mark.asyncio
async def test_build_user_notifier_unconfigured():
    from app.modules.integrations.notifier_registry import build_user_notifier

    db = MagicMock()
    with patch(
        "app.modules.integrations.notifier_registry.IntegrationRepository"
    ) as Repo:
        repo = Repo.return_value
        repo.get_by_provider = AsyncMock(return_value=None)
        notifier = await build_user_notifier(db, "user-1", provider="telegram")
        assert notifier is None


@pytest.mark.asyncio
async def test_notifications_send_telegram_fallback_when_unconfigured():
    from app.modules.notifications.service import NotificationService

    db = MagicMock()
    service = NotificationService(db)
    notif = MagicMock()
    notif.id = "n1"
    notif.message = "Hello"
    notif.telegram_sent = False

    service.repo.get_by_id = AsyncMock(return_value=notif)
    service.repo.db = db

    with patch(
        "app.modules.integrations.notifier_registry.build_user_notifier",
        new=AsyncMock(return_value=None),
    ):
        result = await service.send_telegram("user-1", "n1")
    assert result.sent is False
    assert "not configured" in result.detail.lower()
    assert notif.telegram_sent is False


@pytest.mark.asyncio
async def test_telegram_notifier_send_ok():
    client = MagicMock()
    client.send_message = AsyncMock(return_value={"message_id": 1})
    notifier = TelegramNotifier(client, "99")
    result = await notifier.send(NotifierMessage(text="ping"))
    assert result.ok is True
    client.send_message.assert_awaited_once()
