"""Encrypt, read and update the Garmin connection stored in `integration_connections.config_json`.

Only the personal API key is secret (Fernet-encrypted). Bearer tokens are never stored: each sync
trades the key for a fresh one. `synced_through` is the last date whose health data is fully pulled and
`activities_synced_through` the same for activities; they are separate because Health and Running can each
sync only their own part.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.core.crypto import decrypt, encrypt
from app.modules.integrations.common import load_json_object, mask_secret

logger = logging.getLogger(__name__)

PROVIDER = "garmin"
DISPLAY_NAME = "Garmin"

_UNSET: Any = object()


@dataclass(frozen=True)
class GarminConfig:
    api_key: str  # "" when not connected (or undecryptable)
    key_masked: str
    synced_through: date | None
    activities_synced_through: date | None
    last_sync_message: str | None
    last_sync_ok: bool | None

    @property
    def connected(self) -> bool:
        return bool(self.api_key)


def _date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


def parse_config(config_json: str | None) -> GarminConfig:
    data = load_json_object(config_json, label=PROVIDER)
    key = ""
    if data.get("api_key_enc"):
        try:
            key = decrypt(str(data["api_key_enc"]))
        except ValueError:
            # Fail closed: treat as disconnected rather than using a bad credential.
            logger.warning("Failed to decrypt the Garmin key (tampered or wrong key)")
    ok = data.get("last_sync_ok")
    synced_through = _date(data.get("synced_through"))
    return GarminConfig(
        api_key=key,
        key_masked=str(data.get("key_masked") or "") if key else "",
        synced_through=synced_through,
        # Before the split one cursor covered both, and activities were always pulled first.
        activities_synced_through=_date(data.get("activities_synced_through")) or synced_through,
        last_sync_message=data.get("last_sync_message") or None,
        last_sync_ok=bool(ok) if ok is not None else None,
    )


def serialize_config(
    existing_json: str | None,
    *,
    api_key: Any = _UNSET,
    synced_through: Any = _UNSET,
    activities_synced_through: Any = _UNSET,
    last_sync_message: Any = _UNSET,
    last_sync_ok: Any = _UNSET,
) -> str:
    """Merge updates into the stored config. Omitted fields keep their stored value."""
    data = load_json_object(existing_json, label=PROVIDER)
    if api_key is not _UNSET:
        data["api_key_enc"] = encrypt(api_key) if api_key else ""
        data["key_masked"] = mask_secret(api_key)
    if synced_through is not _UNSET:
        data["synced_through"] = synced_through.isoformat() if synced_through else None
    if activities_synced_through is not _UNSET:
        data["activities_synced_through"] = activities_synced_through.isoformat() if activities_synced_through else None
    if last_sync_message is not _UNSET:
        data["last_sync_message"] = str(last_sync_message)[:300] if last_sync_message else None
    if last_sync_ok is not _UNSET:
        data["last_sync_ok"] = last_sync_ok
    data.pop("api_key", None)  # never persist plaintext, even if a forged config carries it
    return json.dumps(data)
