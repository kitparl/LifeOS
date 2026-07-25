"""Unified inbound Telegram update router for webhook and polling."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.command_handler import handle_command
from app.modules.integrations.telegram import conversation as conv
from app.modules.integrations.telegram.callbacks import CallbackContext, dispatch, parse_callback
from app.modules.integrations.telegram.renderer import Screen, render_screen, send_text

logger = logging.getLogger(__name__)


def _extract_message(update: dict[str, Any]) -> dict[str, Any] | None:
    msg = update.get("message") or update.get("edited_message") or update.get("channel_post")
    return msg if isinstance(msg, dict) else None


def _extract_callback(update: dict[str, Any]) -> dict[str, Any] | None:
    cq = update.get("callback_query")
    return cq if isinstance(cq, dict) else None


async def route_update(
    db: AsyncSession,
    user_id: str,
    expected_chat_id: str,
    update: dict[str, Any],
) -> dict[str, str]:
    """Process one Telegram Update. Caller has already authenticated the connection.

    Returns a small status dict; never raises for user-facing soft errors.
    """
    # --- Callback queries (inline button taps) ---
    cq = _extract_callback(update)
    if cq is not None:
        return await _handle_callback(db, user_id, expected_chat_id, cq)

    # --- Messages (commands, conversation replies, media) ---
    msg = _extract_message(update)
    if msg is None:
        return {"ok": "ignored"}

    chat = msg.get("chat") if isinstance(msg.get("chat"), dict) else {}
    chat_id = str(chat.get("id") or "")
    if not chat_id or chat_id != expected_chat_id:
        logger.warning("Rejected update from unknown chat_id=%s", chat_id)
        return {"ok": "rejected_chat"}

    # Photo / document attachments
    if msg.get("photo") or msg.get("document") or msg.get("voice"):
        from app.modules.integrations.telegram.screens import attachments as att_screens

        screen = await att_screens.handle_media(db, user_id, msg)
        if screen is not None:
            await render_screen(db, user_id, screen)
            return {"ok": "media"}

    text = str(msg.get("text") or "").strip()
    if not text:
        return {"ok": "ignored"}

    # Active conversation takes priority over slash commands (except /cancel)
    if text.lower() in ("/cancel", "cancel"):
        if conv.is_active(user_id):
            screen = conv.cancel(user_id)
            await render_screen(db, user_id, screen, message_id=None)
            return {"ok": "cancelled"}

    if conv.is_active(user_id) and not text.startswith("/"):
        screen = await conv.handle_text(db, user_id, text)
        if screen is not None:
            state = __import__(
                "app.modules.integrations.telegram.state", fromlist=["get_conversation"]
            ).get_conversation(user_id)
            mid = state.message_id if state else None
            await render_screen(db, user_id, screen, message_id=mid if screen.edit else None)
            return {"ok": "conversation"}

    # Slash commands (and free-text falling through to command handler hints)
    reply = await handle_command(db, user_id, text)
    from app.modules.integrations.telegram.renderer import Screen as ScreenCls

    if isinstance(reply, ScreenCls):
        await render_screen(db, user_id, reply)
        return {"ok": "command_screen"}
    if isinstance(reply, str):
        await send_text(db, user_id, reply)
        return {"ok": "command"}
    return {"ok": "processed"}


async def _handle_callback(
    db: AsyncSession,
    user_id: str,
    expected_chat_id: str,
    cq: dict[str, Any],
) -> dict[str, str]:
    msg = cq.get("message") if isinstance(cq.get("message"), dict) else {}
    chat = msg.get("chat") if isinstance(msg.get("chat"), dict) else {}
    chat_id = str(chat.get("id") or "")
    if not chat_id or chat_id != expected_chat_id:
        logger.warning("Rejected callback from unknown chat_id=%s", chat_id)
        return {"ok": "rejected_chat"}

    data = str(cq.get("data") or "")
    callback_id = str(cq.get("id") or "")
    message_id = msg.get("message_id")
    mid = int(message_id) if isinstance(message_id, int) else None

    ns, action, args = parse_callback(data)
    ctx = CallbackContext(
        db=db,
        user_id=user_id,
        chat_id=chat_id,
        message_id=mid,
        callback_id=callback_id,
        data=data,
        namespace=ns,
        action=action,
        args=args,
    )

    # Ensure screen handlers are registered
    import app.modules.integrations.telegram.screens  # noqa: F401

    result = await dispatch(ctx)
    toast: str | None = None
    screen: Screen | None = None
    if isinstance(result, Screen):
        screen = result
    elif isinstance(result, tuple) and len(result) == 2:
        screen, toast = result
    elif isinstance(result, str):
        toast = result

    if screen is not None:
        await render_screen(
            db,
            user_id,
            screen,
            message_id=mid,
            callback_id=callback_id,
            callback_toast=toast,
        )
    elif callback_id:
        # Answer even when no screen (e.g. noop)
        pair = await __import__(
            "app.modules.integrations.telegram.renderer", fromlist=["_client_for_user"]
        )._client_for_user(db, user_id)
        if pair is not None:
            client, _ = pair
            try:
                await client.answer_callback_query(callback_id, text=toast or "")
            except Exception:
                pass
    return {"ok": "callback"}
