"""Cycle 7 — Interactive Telegram bot tests (kernel + screens + outbox markup)."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException

from app.core import crypto
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.callbacks import parse_callback
from app.modules.integrations.telegram.ids import resolve_one, short_id
from app.modules.integrations.telegram.renderer import Screen
from app.modules.integrations.telegram.state import (
    clear_all_for_tests,
    clear_conversation,
    get_conversation,
    put_token,
    get_token,
    start_conversation,
)
from app.modules.integrations.telegram_config import serialize_config


@pytest.fixture(autouse=True)
def _fresh_state(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("INTEGRATION_ENC_KEY", key)
    from app.core.config import get_settings

    get_settings.cache_clear()
    crypto._get_fernet.cache_clear()
    clear_all_for_tests()
    # Ensure screen handlers registered
    import app.modules.integrations.telegram.screens  # noqa: F401

    yield
    clear_all_for_tests()
    crypto._get_fernet.cache_clear()
    get_settings.cache_clear()


def test_short_id_and_resolve():
    class Obj:
        def __init__(self, id, title):
            self.id = id
            self.title = title

    items = [Obj("abcdef12-xxxx", "A"), Obj("zzzzzzzz-yyyy", "B")]
    assert short_id(items[0].id) == "abcdef12"
    assert resolve_one(items, "abcdef12").title == "A"
    assert resolve_one(items, "zzz") is not None
    assert resolve_one(items, "nope") is None


def test_parse_callback():
    ns, action, args = parse_callback("task:done:abcdef12")
    assert ns == "task"
    assert action == "done"
    assert args == ("abcdef12",)


def test_keyboard_callback_limit():
    with pytest.raises(ValueError):
        kb.button("x", "a" * 65)


def test_inline_keyboard_shape():
    markup = kb.inline_keyboard(
        [kb.row(kb.button("A", "nav:home")), kb.nav_row(back="task:list:0")]
    )
    assert "inline_keyboard" in markup
    assert markup["inline_keyboard"][0][0]["callback_data"] == "nav:home"


def test_state_ttl_and_tokens():
    start_conversation("u1", "task_add", "ask_title", data={"x": 1})
    state = get_conversation("u1")
    assert state is not None
    assert state.flow == "task_add"
    token = put_token({"q": "milk"})
    assert get_token(token)["q"] == "milk"
    clear_conversation("u1")
    assert get_conversation("u1") is None


@pytest.mark.asyncio
async def test_handle_command_dashboard_returns_screen():
    from app.modules.integrations.command_handler import handle_command

    db = MagicMock()
    result = await handle_command(db, "user-1", "/dashboard")
    assert isinstance(result, Screen)
    assert "Home" in result.text or "LifeOS" in result.text
    assert result.keyboard is not None


@pytest.mark.asyncio
async def test_handle_command_help_still_text():
    from app.modules.integrations.command_handler import handle_command

    db = MagicMock()
    help_text = await handle_command(db, "user-1", "/help")
    assert isinstance(help_text, str)
    assert "/dashboard" in help_text
    assert "/tasks" in help_text


@pytest.mark.asyncio
async def test_tasks_list_screen_empty():
    from app.modules.integrations.telegram.screens.tasks import tasks_list_screen

    db = MagicMock()
    with patch("app.modules.integrations.telegram.screens.tasks.TaskService") as Svc:
        svc = Svc.return_value
        svc.list_tasks = AsyncMock(return_value=[])
        screen = await tasks_list_screen(db, "u1", 0)
    assert isinstance(screen, Screen)
    assert "No open tasks" in screen.text
    assert screen.keyboard is not None


@pytest.mark.asyncio
async def test_tasks_done_callback():
    from app.modules.integrations.telegram.callbacks import CallbackContext, dispatch

    db = MagicMock()
    task = MagicMock()
    task.id = "abcdef12-3456-7890"
    task.title = "Ship it"
    task.status = "pending"
    task.priority = "medium"
    task.due_date = None

    with patch("app.modules.integrations.telegram.screens.tasks.TaskService") as Svc:
        svc = Svc.return_value
        svc.list_tasks = AsyncMock(side_effect=[[task], [], [], []])
        svc.complete_task = AsyncMock(return_value=task)
        ctx = CallbackContext(
            db=db,
            user_id="u1",
            chat_id="1",
            message_id=10,
            callback_id="cq1",
            data="task:done:abcdef12",
            namespace="task",
            action="done",
            args=("abcdef12",),
        )
        result = await dispatch(ctx)
    assert isinstance(result, tuple)
    screen, toast = result
    assert "Done" in toast
    svc.complete_task.assert_awaited_once()


@pytest.mark.asyncio
async def test_habits_complete_callback():
    from app.modules.integrations.telegram.callbacks import CallbackContext, dispatch

    db = MagicMock()
    habit = MagicMock()
    habit.id = "habit001-xxxx"
    habit.name = "Meditate"
    habit.frequency = "daily"
    habit.completed_today = False
    habit.streak = 3

    completed = MagicMock()
    completed.id = habit.id
    completed.name = habit.name
    completed.frequency = "daily"
    completed.completed_today = True
    completed.streak = 4

    with patch("app.modules.integrations.telegram.screens.habits.HabitService") as Svc:
        svc = Svc.return_value
        svc.list_habits = AsyncMock(side_effect=[[habit], [completed]])
        svc.complete_today = AsyncMock(return_value=completed)
        ctx = CallbackContext(
            db=db,
            user_id="u1",
            chat_id="1",
            message_id=10,
            callback_id="cq1",
            data="habit:done:habit001",
            namespace="habit",
            action="done",
            args=("habit001",),
        )
        result = await dispatch(ctx)
    assert isinstance(result, tuple)
    _, toast = result
    assert "Done" in toast


@pytest.mark.asyncio
async def test_outbox_enqueue_with_markup():
    from app.modules.integrations.outbox_repository import OutboxRepository

    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    repo = OutboxRepository(db)
    markup = {"inline_keyboard": [[{"text": "X", "callback_data": "nav:home"}]]}
    row = await repo.enqueue("u1", "hello", reply_markup=markup)
    assert row.reply_markup_json is not None
    assert "nav:home" in row.reply_markup_json


@pytest.mark.asyncio
async def test_dispatcher_sends_markup():
    from app.modules.integrations.dispatcher import NotificationDispatcher
    from app.modules.integrations.notifier import NotifierResult
    from app.modules.integrations.outbox_models import PENDING, PendingNotification

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
        reply_markup_json='{"inline_keyboard":[[{"text":"Home","callback_data":"nav:home"}]]}',
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
    call_msg = notifier.send.await_args.args[0]
    assert call_msg.reply_markup is not None
    assert "inline_keyboard" in call_msg.reply_markup


@pytest.mark.asyncio
async def test_subscriber_attaches_task_keyboard():
    from app.core.events import TASK_CREATED, EntityCreated
    from app.modules.integrations.subscriber import on_entity_created

    db = MagicMock()
    conn = MagicMock()
    conn.enabled = True
    conn.config_json = serialize_config(
        bot_token="t", chat_id="1", notify_on=["task_created"]
    )

    with (
        patch("app.modules.integrations.subscriber.IntegrationRepository") as Repo,
        patch("app.modules.integrations.subscriber.OutboxRepository") as Outbox,
    ):
        Repo.return_value.get_by_provider = AsyncMock(return_value=conn)
        Outbox.return_value.enqueue = AsyncMock()
        await on_entity_created(
            db,
            EntityCreated(
                TASK_CREATED, "u1", "abcdef12-3456", "Buy milk", when="2026-07-25", module="tasks"
            ),
        )
    kwargs = Outbox.return_value.enqueue.await_args.kwargs
    assert kwargs.get("reply_markup") is not None
    assert "task:done:abcdef12" in str(kwargs["reply_markup"])


@pytest.mark.asyncio
async def test_digest_has_section_buttons():
    from app.modules.integrations.digest_service import DigestContent, format_digest

    msg = format_digest(DigestContent(pending_tasks=["A"]))
    assert msg.reply_markup is not None
    assert any(
        b.get("callback_data") == "task:list:0"
        for row in msg.reply_markup["inline_keyboard"]
        for b in row
    )


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
async def test_route_update_callback_nav_home():
    from app.modules.integrations.telegram.update_router import route_update

    db = MagicMock()
    with patch(
        "app.modules.integrations.telegram.update_router.render_screen",
        new=AsyncMock(return_value={"ok": True}),
    ) as render:
        result = await route_update(
            db,
            "u1",
            "111",
            {
                "callback_query": {
                    "id": "cq1",
                    "data": "nav:home",
                    "message": {"message_id": 5, "chat": {"id": 111}},
                }
            },
        )
    assert result["ok"] == "callback"
    render.assert_awaited()


@pytest.mark.asyncio
async def test_ai_parse_and_create_task_fallback():
    from app.modules.ai.service import AiService

    db = MagicMock()
    created = MagicMock()
    created.title = "Call the dentist"
    created.due_date = datetime.combine(date.today(), time(12, 0), tzinfo=timezone.utc)

    with patch("app.modules.tasks.service.TaskService") as Svc:
        Svc.return_value.create_task = AsyncMock(return_value=created)
        svc = AiService(db)
        svc.provider = MagicMock()
        svc.provider.enabled = False
        task = await svc.parse_and_create_task("u1", "remind me to Call the dentist")
    assert task.title == "Call the dentist"


@pytest.mark.asyncio
async def test_telegram_client_send_with_markup():
    from app.modules.integrations.telegram_client import TelegramClient

    client = TelegramClient("123:ABC")
    with patch.object(client, "_post", new=AsyncMock(return_value={"message_id": 1})) as post:
        await client.send_message(
            "1",
            "hi",
            reply_markup={"inline_keyboard": [[{"text": "H", "callback_data": "nav:home"}]]},
        )
    payload = post.await_args.args[1]
    assert "reply_markup" in payload


@pytest.mark.asyncio
async def test_handle_command_done_still_works():
    from app.modules.integrations.command_handler import handle_command

    db = MagicMock()
    msg = await handle_command(db, "user-1", "/done")
    assert "Usage" in msg
