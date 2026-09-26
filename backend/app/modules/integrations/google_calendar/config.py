"""Encrypt/decrypt and mask Google Calendar integration config stored in config_json.

Only the refresh token is secret (Fernet-encrypted). Everything else is plain
bookkeeping. Access tokens are never persisted — a fresh one is minted per sync/push.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Literal

from app.core.crypto import decrypt, encrypt
from app.modules.integrations.common import load_json_object

logger = logging.getLogger(__name__)

SyncDirection = Literal["google_to_lifeos", "two_way"]
SYNC_DIRECTIONS: tuple[str, ...] = ("google_to_lifeos", "two_way")
DEFAULT_DIRECTION: SyncDirection = "google_to_lifeos"
DEFAULT_CALENDAR_ID = "primary"

SCOPE_READONLY = "https://www.googleapis.com/auth/calendar.events.readonly"
SCOPE_READWRITE = "https://www.googleapis.com/auth/calendar.events"


@dataclass(frozen=True)
class GoogleCalendarConfig:
    refresh_token: str  # "" when not connected (or undecryptable)
    scope: str
    sync_direction: str
    calendar_id: str
    time_zone: str | None
    last_sync_message: str | None
    last_sync_ok: bool | None

    @property
    def connected(self) -> bool:
        return bool(self.refresh_token)

    @property
    def can_write(self) -> bool:
        # The read-only scope URL shares a prefix with the read/write one — compare whole tokens.
        return SCOPE_READWRITE in self.scope.split()


def _direction(value: Any) -> str:
    return value if value in SYNC_DIRECTIONS else DEFAULT_DIRECTION


def parse_config(config_json: str | None) -> GoogleCalendarConfig:
    data = load_json_object(config_json, label="google_calendar")
    token = ""
    if data.get("refresh_token_enc"):
        try:
            token = decrypt(str(data["refresh_token_enc"]))
        except ValueError:
            # Fail closed: treat as disconnected rather than using a bad credential.
            logger.warning("Failed to decrypt google_calendar refresh token (tampered or wrong key)")
            token = ""
    ok = data.get("last_sync_ok")
    return GoogleCalendarConfig(
        refresh_token=token,
        scope=str(data.get("scope") or ""),
        sync_direction=_direction(data.get("sync_direction")),
        calendar_id=str(data.get("calendar_id") or DEFAULT_CALENDAR_ID),
        time_zone=str(data["time_zone"])[:64] if data.get("time_zone") else None,
        last_sync_message=data.get("last_sync_message") or None,
        last_sync_ok=bool(ok) if ok is not None else None,
    )


_UNSET: Any = object()


def serialize_config(
    existing_json: str | None,
    *,
    refresh_token: str | None = None,
    scope: str | None = None,
    sync_direction: str | None = None,
    time_zone: str | None = None,
    last_sync_message: Any = _UNSET,
    last_sync_ok: Any = _UNSET,
) -> str:
    """Merge updates into the existing config. Omitted fields keep their stored value."""
    data = load_json_object(existing_json, label="google_calendar")
    if refresh_token is not None:
        data["refresh_token_enc"] = encrypt(refresh_token) if refresh_token else ""
    if scope is not None:
        data["scope"] = scope
    if sync_direction is not None:
        data["sync_direction"] = _direction(sync_direction)
    if time_zone is not None:
        data["time_zone"] = time_zone[:64]
    data.setdefault("sync_direction", DEFAULT_DIRECTION)
    data.setdefault("calendar_id", DEFAULT_CALENDAR_ID)
    if last_sync_message is not _UNSET:
        data["last_sync_message"] = (str(last_sync_message)[:300] if last_sync_message else None)
    if last_sync_ok is not _UNSET:
        data["last_sync_ok"] = last_sync_ok
    # Never persist plaintext secrets even if a legacy/forged key is present.
    data.pop("refresh_token", None)
    data.pop("access_token", None)
    return json.dumps(data)
