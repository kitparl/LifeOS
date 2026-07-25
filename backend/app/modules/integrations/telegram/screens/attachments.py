"""Photo / document / voice attachments onto tasks or notes (Phase 7)."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.files.service import FileService
from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.navigation import back_home
from app.modules.integrations.telegram.renderer import Screen
from app.modules.integrations.telegram.state import get_conversation, get_token, put_token, start_conversation
from app.modules.integrations.telegram_client import TelegramClient, TelegramClientError
from app.modules.integrations.telegram_config import parse_config
from app.modules.integrations.repository import IntegrationRepository

logger = logging.getLogger(__name__)


async def _client(db: AsyncSession, user_id: str) -> TelegramClient | None:
    conn = await IntegrationRepository(db).get_by_provider(user_id, "telegram")
    if conn is None or not conn.enabled:
        return None
    cfg = parse_config(conn.config_json)
    if cfg is None:
        return None
    return TelegramClient(cfg.bot_token)


def _pick_file(msg: dict[str, Any]) -> tuple[str, str, str] | None:
    """Return (file_id, filename, content_type) or None."""
    if msg.get("document") and isinstance(msg["document"], dict):
        doc = msg["document"]
        return (
            str(doc.get("file_id") or ""),
            str(doc.get("file_name") or "document.bin"),
            str(doc.get("mime_type") or "application/octet-stream"),
        )
    photos = msg.get("photo")
    if isinstance(photos, list) and photos:
        # Largest photo last
        photo = photos[-1] if isinstance(photos[-1], dict) else None
        if photo:
            return str(photo.get("file_id") or ""), "photo.jpg", "image/jpeg"
    voice = msg.get("voice")
    if isinstance(voice, dict):
        return str(voice.get("file_id") or ""), "voice.ogg", str(voice.get("mime_type") or "audio/ogg")
    return None


async def handle_media(db: AsyncSession, user_id: str, msg: dict[str, Any]) -> Screen | None:
    """Handle inbound photo/document/voice. Uses active conversation target if set."""
    picked = _pick_file(msg)
    if picked is None:
        return None
    file_id, filename, content_type = picked
    if not file_id:
        return None

    client = await _client(db, user_id)
    if client is None:
        return Screen(text="Telegram not configured.")

    try:
        info = await client.get_file(file_id)
        path = info.get("file_path") if isinstance(info, dict) else None
        if not path:
            return Screen(text="Could not resolve file path from Telegram.")
        content = await client.download_file(str(path))
    except TelegramClientError as exc:
        logger.warning("Attachment download failed: %s", exc)
        return Screen(text=f"Download failed: {exc}")

    state = get_conversation(user_id)
    module = "telegram"
    entity_id = None
    caption = str(msg.get("caption") or "").strip()

    if state and state.flow == "attach" and state.data.get("entity_id"):
        module = state.data.get("module") or "tasks"
        entity_id = state.data.get("entity_id")

    record = await FileService(db).upload(
        user_id,
        filename=filename,
        content=content,
        content_type=content_type,
        module=module,
        entity_id=entity_id,
    )

    target = f"{module}/{entity_id}" if entity_id else "unlinked (Telegram)"
    extra = f"\nCaption: {tpl.esc(caption)}" if caption else ""
    return Screen(
        text=tpl.join_blocks(
            tpl._header("Attachment saved"),
            f"<b>{tpl.esc(filename)}</b> ({len(content)} bytes)\n"
            f"Linked to: {tpl.esc(target)}{extra}",
        ),
        keyboard=kb.inline_keyboard([back_home()]),
    )


async def begin_attach_to_task(db: AsyncSession, user_id: str, task_id: str, *, message_id: int | None = None) -> Screen:
    start_conversation(
        user_id,
        "attach",
        "wait_file",
        data={"module": "tasks", "entity_id": task_id},
        message_id=message_id,
    )
    return Screen(
        text=tpl.join_blocks(
            tpl._header("Attach file"),
            "Send a photo, document, or voice note.\nOr /cancel.",
        ),
        keyboard=kb.inline_keyboard([back_home()]),
    )
