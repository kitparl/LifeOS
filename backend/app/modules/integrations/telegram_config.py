"""Encrypt/decrypt and mask Telegram integration config stored in config_json.

Persisted shape:
  { "bot_token_enc": "<fernet>", "chat_id_enc": "<fernet>" }

Plaintext values exist only in memory after parse_config().
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.core.crypto import decrypt, encrypt

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DecryptedTelegramConfig:
    bot_token: str
    chat_id: str


@dataclass(frozen=True)
class MaskedTelegramConfig:
    configured: bool
    bot_token_masked: str | None
    chat_id: str | None


def _mask_token(token: str) -> str:
    if not token:
        return ""
    if len(token) <= 4:
        return "****"
    return f"****{token[-4:]}"


def serialize_config(
    *,
    bot_token: str | None = None,
    chat_id: str | None = None,
    existing_json: str | None = None,
) -> str:
    """Build encrypted config_json. Unset fields preserve existing encrypted values."""
    existing: dict[str, Any] = {}
    if existing_json:
        try:
            parsed = json.loads(existing_json)
            if isinstance(parsed, dict):
                existing = parsed
        except json.JSONDecodeError:
            existing = {}

    token_enc = existing.get("bot_token_enc")
    chat_enc = existing.get("chat_id_enc")

    # Backward-compatible: migrate plaintext keys if present
    if not token_enc and existing.get("bot_token"):
        token_enc = encrypt(str(existing["bot_token"]))
    if not chat_enc and existing.get("chat_id"):
        chat_enc = encrypt(str(existing["chat_id"]))

    if bot_token is not None and bot_token.strip():
        token_enc = encrypt(bot_token.strip())
    if chat_id is not None and chat_id.strip():
        chat_enc = encrypt(chat_id.strip())

    payload = {
        "bot_token_enc": token_enc or "",
        "chat_id_enc": chat_enc or "",
    }
    return json.dumps(payload)


def parse_config(config_json: str | None) -> DecryptedTelegramConfig | None:
    """Decrypt config in memory. Returns None if incomplete or invalid."""
    if not config_json:
        return None
    try:
        data = json.loads(config_json)
    except json.JSONDecodeError:
        logger.warning("Invalid telegram config_json (not JSON)")
        return None
    if not isinstance(data, dict):
        return None

    token = ""
    chat = ""
    try:
        if data.get("bot_token_enc"):
            token = decrypt(str(data["bot_token_enc"]))
        elif data.get("bot_token"):
            token = str(data["bot_token"])
        if data.get("chat_id_enc"):
            chat = decrypt(str(data["chat_id_enc"]))
        elif data.get("chat_id"):
            chat = str(data["chat_id"])
    except ValueError:
        logger.warning("Failed to decrypt telegram config (tampered or wrong key)")
        return None

    if not token.strip() or not chat.strip():
        return None
    return DecryptedTelegramConfig(bot_token=token.strip(), chat_id=chat.strip())


def mask_config(config_json: str | None) -> MaskedTelegramConfig:
    """Public-safe view: never returns raw bot_token."""
    parsed = parse_config(config_json)
    if parsed is None:
        # Still try to surface chat_id from encrypted blob without token
        chat_public: str | None = None
        if config_json:
            try:
                data = json.loads(config_json)
                if isinstance(data, dict):
                    if data.get("chat_id_enc"):
                        try:
                            chat_public = decrypt(str(data["chat_id_enc"]))
                        except ValueError:
                            chat_public = None
                    elif data.get("chat_id"):
                        chat_public = str(data["chat_id"])
            except json.JSONDecodeError:
                pass
        return MaskedTelegramConfig(configured=False, bot_token_masked=None, chat_id=chat_public)
    return MaskedTelegramConfig(
        configured=True,
        bot_token_masked=_mask_token(parsed.bot_token),
        chat_id=parsed.chat_id,
    )
