"""Phase 2 tests: commands, outbox dispatcher, prefs, schedule, webhook auth."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException

from app.core import crypto
from app.core.events import (
    TASK_CREATED,
    EntityCreated,
    event_bus,
)
from app.modules.integrations.command_handler import handle_command
from app.modules.integrations.outbox_models import FAILED, PENDING, PendingNotification
from app.modules.integrations.outbox_repository import OutboxRepository
from app.modules.integrations.scheduler import _cron_for_prefs
from app.modules.integrations.subscriber import format_entity_message
from app.modules.integrations.telegram_config import (
    TelegramPreferences,
    parse_preferences,
    serialize_config,
)


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


def test_preferences_round_trip():
    raw = serialize_config(
        bot_token="123:ABC",
        chat_id="99",
        notify_on=["task_created", "race_added"],
        digest_enabled=True,
        digest_time="9:30",
        digest_frequency="weekdays",
        digest_weekday=2,
        timezone="Asia/Kolkata",
    )
    prefs = parse_preferences(raw)
    assert prefs.notify_on == ["task_created", "race_added"]
    assert prefs.digest_enabled is True
    assert prefs.digest_time == "09:30"
    assert prefs.digest_frequency == "weekdays"
    assert prefs.digest_weekday == 2
    assert prefs.timezone == "Asia/Kolkata"

    # Partial update preserves prefs
    raw2 = serialize_config(chat_id="100", existing_json=raw)
    prefs2 = parse_preferences(raw2)
    assert prefs2.notify_on == ["task_created", "race_added"]
    assert prefs2.digest_enabled is True


def test_preferences_reject_unknown_events():
    raw = serialize_config(
        bot_token="t",
        chat_id="1",
        notify_on=["task_created", "not_a_real_event"],
    )
    prefs = parse_preferences(raw)
    assert prefs.notify_on == ["task_created"]


def test_format_entity_messages():
    assert "New task added: Buy milk" in format_entity_message(
        EntityCreated(TASK_CREATED, "u1", "id1", "Buy milk", when="2026-07-25", module="tasks")
    )
    assert "due 2026-07-25" in format_entity_message(
        EntityCreated(TASK_CREATED, "u1", "id1", "Buy milk", when="2026-07-25", module="tasks")
    )


def test_cron_for_prefs_daily_and_weekly():
    daily = _cron_for_prefs(
        TelegramPreferences(digest_time="08:00", digest_frequency="daily", timezone="UTC")
    )
    assert daily is not None
    weekly = _cron_for_prefs(
        TelegramPreferences(
            digest_time="07:15",
            digest_frequency="weekly",
            digest_weekday=0,
            timezone="Asia/Kolkata",
        )
    )
    assert weekly is not None
    weekdays = _cron_for_prefs(
        TelegramPreferences(digest_time="06:00", digest_frequency="weekdays", timezone="UTC")
    )
    assert weekdays is not None


@pytest.mark.asyncio
async def test_handle_command_help_and_unknown():
    db = MagicMock()
    help_text = await handle_command(db, "user-1", "/help")
    assert "/tasks" in help_text
    unknown = await handle_command(db, "user-1", "/nope")
    assert "Unknown" in unknown or "help" in unknown.lower()


@pytest.mark.asyncio
async def test_handle_command_done_requires_id():
    db = MagicMock()
    msg = await handle_command(db, "user-1", "/done")
    assert "Usage" in msg


@pytest.mark.asyncio
async def test_handle_command_done_completes_match():
    db = MagicMock()
    task = MagicMock()
    task.id = "abcdef12-3456"
    task.title = "Ship feature"
    task.status = "pending"
    task.due_date = None

    with (
        patch("app.modules.tasks.repository.TaskRepository") as Repo,
        patch("app.modules.tasks.service.TaskService") as Svc,
    ):
        repo = Repo.return_value
        repo.list_tasks = AsyncMock(side_effect=[([task], 1), ([], 0)])
        svc = Svc.return_value
        svc.complete_task = AsyncMock(return_value=MagicMock())
        msg = await handle_command(db, "user-1", "/done abcdef12")
    assert "Done" in msg
    assert "Ship feature" in msg
    svc.complete_task.assert_awaited_once()


@pytest.mark.asyncio
async def test_outbox_mark_sent_and_failed_retry():
    db = MagicMock()
    db.flush = AsyncMock()
    repo = OutboxRepository(db)

    row = PendingNotification(
        id="n1",
        user_id="u1",
        text="hi",
        status=PENDING,
        attempts=0,
        max_attempts=2,
    )
    await repo.mark_sent(row)
    assert row.status == "sent"
    assert row.attempts == 1
    assert row.sent_at is not None

    row2 = PendingNotification(
        id="n2",
        user_id="u1",
        text="hi",
        status=PENDING,
        attempts=0,
        max_attempts=2,
    )
    await repo.mark_failed(row2, "boom")
    assert row2.status == PENDING  # still retryable
    assert row2.attempts == 1
    await repo.mark_failed(row2, "boom again")
    assert row2.status == FAILED
    assert row2.attempts == 2


@pytest.mark.asyncio
async def test_dispatcher_marks_sent():
    from app.modules.integrations.dispatcher import NotificationDispatcher
    from app.modules.integrations.notifier import NotifierResult

    db = MagicMock()
    db.commit = AsyncMock()
    row = PendingNotification(
        id="n1",
        user_id="u1",
        channel="telegram",
        text="hello",
        status=PENDING,
        attempts=0,
        max_attempts=5,
    )
    dispatcher = NotificationDispatcher(db)
    dispatcher.repo.fetch_dispatchable = AsyncMock(return_value=[row])
    dispatcher.repo.mark_sent = AsyncMock()
    dispatcher.repo.mark_failed = AsyncMock()

    notifier = MagicMock()
    notifier.send = AsyncMock(return_value=NotifierResult(ok=True, detail="ok"))

    with patch(
        "app.modules.integrations.dispatcher.build_user_notifier",
        new=AsyncMock(return_value=notifier),
    ):
        sent = await dispatcher.dispatch_pending()
    assert sent == 1
    dispatcher.repo.mark_sent.assert_awaited_once()


@pytest.mark.asyncio
async def test_webhook_rejects_unknown_secret():
    from app.modules.integrations.webhook_service import TelegramWebhookService

    db = MagicMock()
    svc = TelegramWebhookService(db)
    svc.repo.get_by_webhook_secret = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await svc.handle_update("bad-secret", {"message": {"text": "/help", "chat": {"id": 1}}})
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_webhook_rejects_unknown_chat():
    from app.modules.integrations.webhook_service import TelegramWebhookService

    db = MagicMock()
    conn = MagicMock()
    conn.enabled = True
    conn.webhook_secret = "sec"
    conn.user_id = "u1"
    conn.config_json = serialize_config(bot_token="tok", chat_id="111")

    svc = TelegramWebhookService(db)
    svc.repo.get_by_webhook_secret = AsyncMock(return_value=conn)

    with pytest.raises(HTTPException) as exc:
        await svc.handle_update(
            "sec",
            {"message": {"text": "/help", "chat": {"id": 999}}},
            header_secret="sec",
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_event_bus_swallows_handler_errors():
    async def bad_handler(db, event):
        raise RuntimeError("boom")

    bus_handlers_before = list(event_bus._handlers)
    event_bus.subscribe(bad_handler)
    try:
        await event_bus.emit(
            MagicMock(),
            EntityCreated(TASK_CREATED, "u", "e", "t", module="tasks"),
        )
    finally:
        event_bus._handlers = bus_handlers_before
