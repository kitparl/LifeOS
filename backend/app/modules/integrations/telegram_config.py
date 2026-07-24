"""Encrypt/decrypt and mask Telegram integration config stored in config_json.

Persisted shape:
  {
    "bot_token_enc": "<fernet>",
    "chat_id_enc": "<fernet>",
    "notify_on": ["task_created", ...],
    "digest_enabled": true,
    "digest_time": "08:00",
    "digest_frequency": "daily",
    "digest_weekday": 0,
    "timezone": "UTC"
  }

Plaintext secrets exist only in memory after parse_config().
Preferences (notify_on, digest_*) are stored as plaintext alongside encrypted secrets.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.core.crypto import decrypt, encrypt
from app.core.events import ALL_EVENT_TYPES, DEFAULT_NOTIFY_ON

logger = logging.getLogger(__name__)

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
_DIGEST_FREQUENCIES = frozenset({"daily", "weekdays", "weekly"})


@dataclass(frozen=True)
class DecryptedTelegramConfig:
    bot_token: str
    chat_id: str


@dataclass(frozen=True)
class MaskedTelegramConfig:
    configured: bool
    bot_token_masked: str | None
    chat_id: str | None


@dataclass(frozen=True)
class TelegramPreferences:
    notify_on: list[str] = field(default_factory=lambda: list(DEFAULT_NOTIFY_ON))
    digest_enabled: bool = False
    digest_time: str = "08:00"
    digest_frequency: str = "daily"  # daily | weekdays | weekly
    digest_weekday: int = 0  # 0=Mon … 6=Sun (APScheduler / ISO-ish)
    timezone: str = "UTC"


def _mask_token(token: str) -> str:
    if not token:
        return ""
    if len(token) <= 4:
        return "****"
    return f"****{token[-4:]}"


def _load_json(config_json: str | None) -> dict[str, Any]:
    if not config_json:
        return {}
    try:
        parsed = json.loads(config_json)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _normalize_notify_on(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return list(DEFAULT_NOTIFY_ON)
    allowed = set(ALL_EVENT_TYPES)
    cleaned = [str(x) for x in raw if str(x) in allowed]
    return cleaned


def _normalize_time(raw: Any, default: str = "08:00") -> str:
    if not isinstance(raw, str) or not _TIME_RE.match(raw.strip()):
        return default
    h, m = raw.strip().split(":")
    return f"{int(h):02d}:{int(m):02d}"


def _normalize_weekday(raw: Any, default: int = 0) -> int:
    try:
        v = int(raw)
        return v if 0 <= v <= 6 else default
    except (TypeError, ValueError):
        return default


def parse_preferences(config_json: str | None) -> TelegramPreferences:
    data = _load_json(config_json)
    freq = str(data.get("digest_frequency") or "daily").lower()
    if freq not in _DIGEST_FREQUENCIES:
        freq = "daily"
    tz = str(data.get("timezone") or "UTC").strip() or "UTC"
    return TelegramPreferences(
        notify_on=_normalize_notify_on(data.get("notify_on")),
        digest_enabled=bool(data.get("digest_enabled", False)),
        digest_time=_normalize_time(data.get("digest_time")),
        digest_frequency=freq,
        digest_weekday=_normalize_weekday(data.get("digest_weekday")),
        timezone=tz,
    )


def serialize_config(
    *,
    bot_token: str | None = None,
    chat_id: str | None = None,
    existing_json: str | None = None,
    notify_on: list[str] | None = None,
    digest_enabled: bool | None = None,
    digest_time: str | None = None,
    digest_frequency: str | None = None,
    digest_weekday: int | None = None,
    timezone: str | None = None,
) -> str:
    """Build encrypted config_json. Unset fields preserve existing values."""
    existing = _load_json(existing_json)

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

    prefs = parse_preferences(existing_json)
    payload: dict[str, Any] = {
        "bot_token_enc": token_enc or "",
        "chat_id_enc": chat_enc or "",
        "notify_on": _normalize_notify_on(notify_on) if notify_on is not None else prefs.notify_on,
        "digest_enabled": bool(digest_enabled) if digest_enabled is not None else prefs.digest_enabled,
        "digest_time": _normalize_time(digest_time) if digest_time is not None else prefs.digest_time,
        "digest_frequency": (
            str(digest_frequency).lower()
            if digest_frequency is not None and str(digest_frequency).lower() in _DIGEST_FREQUENCIES
            else prefs.digest_frequency
        ),
        "digest_weekday": (
            _normalize_weekday(digest_weekday) if digest_weekday is not None else prefs.digest_weekday
        ),
        "timezone": (timezone.strip() if timezone and timezone.strip() else prefs.timezone),
    }
    return json.dumps(payload)


def parse_config(config_json: str | None) -> DecryptedTelegramConfig | None:
    """Decrypt config in memory. Returns None if incomplete or invalid."""
    data = _load_json(config_json)
    if not data:
        if config_json:
            logger.warning("Invalid telegram config_json (not JSON)")
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
        chat_public: str | None = None
        data = _load_json(config_json)
        if data.get("chat_id_enc"):
            try:
                chat_public = decrypt(str(data["chat_id_enc"]))
            except ValueError:
                chat_public = None
        elif data.get("chat_id"):
            chat_public = str(data["chat_id"])
        return MaskedTelegramConfig(configured=False, bot_token_masked=None, chat_id=chat_public)
    return MaskedTelegramConfig(
        configured=True,
        bot_token_masked=_mask_token(parsed.bot_token),
        chat_id=parsed.chat_id,
    )
