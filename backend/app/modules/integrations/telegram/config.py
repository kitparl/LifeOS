"""Encrypt/decrypt and mask Telegram integration config stored in config_json.

Persisted shape (additive — digest_* retained for backward compatibility):
  {
    "bot_token_enc": "<fernet>",
    "chat_id_enc": "<fernet>",
    "notify_on": ["task_created", ...],
    "digest_enabled": true,
    "digest_time": "08:00",
    "digest_frequency": "daily",
    "digest_weekday": 0,
    "timezone": "Asia/Kolkata",
    "morning_enabled": true,
    "morning_time": "06:00",
    "midday_enabled": true,
    "midday_time": "12:30",
    "night_enabled": true,
    "night_time": "22:00",
    "weekly_enabled": true,
    "weekly_time": "18:00",
    "weekly_weekday": 6,
    "ai_briefing_enabled": false,
    "ai_briefing_time": "08:00",
    "birthday_reminders_enabled": true,
    "immutable_reminders_enabled": true,
    "routine_reminders_enabled": true
  }

Plaintext secrets exist only in memory after parse_config().
Preferences are stored as plaintext alongside encrypted secrets.
morning_* falls back to digest_* when the new keys are absent.
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
DEFAULT_TIMEZONE = "Asia/Kolkata"
# Marks a config whose legacy hardcoded "UTC" timezone has been rewritten once.
# Without it the startup backfill would keep overwriting a deliberate UTC choice.
TZ_BACKFILL_KEY = "tz_backfilled"


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
    # Legacy digest_* (kept for API compatibility; mapped to/from morning_*)
    digest_enabled: bool = False
    digest_time: str = "06:00"
    digest_frequency: str = "daily"  # daily | weekdays | weekly
    digest_weekday: int = 0  # 0=Mon … 6=Sun
    timezone: str = DEFAULT_TIMEZONE
    # Scheduled reports (Cycle 8)
    morning_enabled: bool = True
    morning_time: str = "06:00"
    midday_enabled: bool = True
    midday_time: str = "12:30"
    night_enabled: bool = True
    night_time: str = "22:00"
    weekly_enabled: bool = True
    weekly_time: str = "18:00"
    weekly_weekday: int = 6  # Sunday
    ai_briefing_enabled: bool = False
    ai_briefing_time: str = "08:00"
    birthday_reminders_enabled: bool = True
    immutable_reminders_enabled: bool = True
    routine_reminders_enabled: bool = True


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


def _normalize_time(raw: Any, default: str = "06:00") -> str:
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


def _bool_or(data: dict[str, Any], key: str, default: bool) -> bool:
    if key not in data:
        return default
    return bool(data[key])


def parse_preferences(config_json: str | None) -> TelegramPreferences:
    data = _load_json(config_json)
    freq = str(data.get("digest_frequency") or "daily").lower()
    if freq not in _DIGEST_FREQUENCIES:
        freq = "daily"
    tz = str(data.get("timezone") or DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE

    # Legacy digest_* — used as morning fallback when morning_* keys are absent.
    digest_enabled = bool(data.get("digest_enabled", False))
    digest_time = _normalize_time(data.get("digest_time"), "06:00")

    if "morning_enabled" in data:
        morning_enabled = bool(data["morning_enabled"])
    else:
        morning_enabled = digest_enabled if "digest_enabled" in data else True

    if "morning_time" in data:
        morning_time = _normalize_time(data.get("morning_time"), "06:00")
    else:
        morning_time = digest_time if "digest_time" in data else "06:00"

    return TelegramPreferences(
        notify_on=_normalize_notify_on(data.get("notify_on")),
        digest_enabled=digest_enabled if "digest_enabled" in data else morning_enabled,
        digest_time=digest_time if "digest_time" in data else morning_time,
        digest_frequency=freq,
        digest_weekday=_normalize_weekday(data.get("digest_weekday")),
        timezone=tz,
        morning_enabled=morning_enabled,
        morning_time=morning_time,
        midday_enabled=_bool_or(data, "midday_enabled", True),
        midday_time=_normalize_time(data.get("midday_time"), "12:30"),
        night_enabled=_bool_or(data, "night_enabled", True),
        night_time=_normalize_time(data.get("night_time"), "22:00"),
        weekly_enabled=_bool_or(data, "weekly_enabled", True),
        weekly_time=_normalize_time(data.get("weekly_time"), "18:00"),
        weekly_weekday=_normalize_weekday(data.get("weekly_weekday"), 6),
        ai_briefing_enabled=_bool_or(data, "ai_briefing_enabled", False),
        ai_briefing_time=_normalize_time(data.get("ai_briefing_time"), "08:00"),
        birthday_reminders_enabled=_bool_or(data, "birthday_reminders_enabled", True),
        immutable_reminders_enabled=_bool_or(data, "immutable_reminders_enabled", True),
        routine_reminders_enabled=_bool_or(data, "routine_reminders_enabled", True),
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
    morning_enabled: bool | None = None,
    morning_time: str | None = None,
    midday_enabled: bool | None = None,
    midday_time: str | None = None,
    night_enabled: bool | None = None,
    night_time: str | None = None,
    weekly_enabled: bool | None = None,
    weekly_time: str | None = None,
    weekly_weekday: int | None = None,
    ai_briefing_enabled: bool | None = None,
    ai_briefing_time: str | None = None,
    birthday_reminders_enabled: bool | None = None,
    immutable_reminders_enabled: bool | None = None,
    routine_reminders_enabled: bool | None = None,
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

    # Resolve morning from explicit morning_* or digest_* updates
    resolved_morning_enabled = (
        bool(morning_enabled)
        if morning_enabled is not None
        else (bool(digest_enabled) if digest_enabled is not None else prefs.morning_enabled)
    )
    resolved_morning_time = (
        _normalize_time(morning_time)
        if morning_time is not None
        else (_normalize_time(digest_time) if digest_time is not None else prefs.morning_time)
    )

    payload: dict[str, Any] = {
        "bot_token_enc": token_enc or "",
        "chat_id_enc": chat_enc or "",
        "notify_on": _normalize_notify_on(notify_on) if notify_on is not None else prefs.notify_on,
        # Keep digest_* in sync with morning_* for legacy clients
        "digest_enabled": resolved_morning_enabled,
        "digest_time": resolved_morning_time,
        "digest_frequency": (
            str(digest_frequency).lower()
            if digest_frequency is not None and str(digest_frequency).lower() in _DIGEST_FREQUENCIES
            else prefs.digest_frequency
        ),
        "digest_weekday": (
            _normalize_weekday(digest_weekday) if digest_weekday is not None else prefs.digest_weekday
        ),
        "timezone": (timezone.strip() if timezone and timezone.strip() else prefs.timezone),
        "morning_enabled": resolved_morning_enabled,
        "morning_time": resolved_morning_time,
        "midday_enabled": bool(midday_enabled) if midday_enabled is not None else prefs.midday_enabled,
        "midday_time": _normalize_time(midday_time, "12:30") if midday_time is not None else prefs.midday_time,
        "night_enabled": bool(night_enabled) if night_enabled is not None else prefs.night_enabled,
        "night_time": _normalize_time(night_time, "22:00") if night_time is not None else prefs.night_time,
        "weekly_enabled": bool(weekly_enabled) if weekly_enabled is not None else prefs.weekly_enabled,
        "weekly_time": _normalize_time(weekly_time, "18:00") if weekly_time is not None else prefs.weekly_time,
        "weekly_weekday": (
            _normalize_weekday(weekly_weekday, 6) if weekly_weekday is not None else prefs.weekly_weekday
        ),
        "ai_briefing_enabled": (
            bool(ai_briefing_enabled) if ai_briefing_enabled is not None else prefs.ai_briefing_enabled
        ),
        "ai_briefing_time": (
            _normalize_time(ai_briefing_time, "08:00")
            if ai_briefing_time is not None
            else prefs.ai_briefing_time
        ),
        "birthday_reminders_enabled": (
            bool(birthday_reminders_enabled)
            if birthday_reminders_enabled is not None
            else prefs.birthday_reminders_enabled
        ),
        "immutable_reminders_enabled": (
            bool(immutable_reminders_enabled)
            if immutable_reminders_enabled is not None
            else prefs.immutable_reminders_enabled
        ),
        "routine_reminders_enabled": (
            bool(routine_reminders_enabled)
            if routine_reminders_enabled is not None
            else prefs.routine_reminders_enabled
        ),
    }
    if existing.get(TZ_BACKFILL_KEY):
        payload[TZ_BACKFILL_KEY] = True
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
