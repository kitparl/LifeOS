"""Helpers shared by the per-provider integration configs (AI, Wordnik, news, GitHub, Google Calendar, Telegram)."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.core.crypto import decrypt, encrypt

logger = logging.getLogger(__name__)


def load_json_object(config_json: str | None, *, label: str) -> dict[str, Any]:
    """Parse a stored ``config_json`` column; anything but a JSON object reads as empty."""
    if not config_json:
        return {}
    try:
        parsed = json.loads(config_json)
    except json.JSONDecodeError:
        logger.warning("Invalid %s config_json (not JSON)", label)
        return {}
    return parsed if isinstance(parsed, dict) else {}


def load_api_keys(config_json: str | None, *, label: str) -> list[str]:
    """Decrypted keys from ``{"keys_enc": [...]}``, in saved order.

    A legacy single ``api_key_enc`` reads as one key. Undecryptable entries are skipped.
    """
    data = load_json_object(config_json, label=label)
    encrypted = list(data.get("keys_enc") or [])
    if not encrypted and data.get("api_key_enc"):
        encrypted = [data["api_key_enc"]]
    keys: list[str] = []
    for item in encrypted:
        try:
            key = decrypt(str(item)).strip()
        except ValueError:
            logger.warning("Failed to decrypt a %s key (tampered or wrong key)", label)
            continue
        if key and key not in keys:
            keys.append(key)
    return keys


def serialize_api_keys(keys: list[str]) -> str:
    """``{"keys_enc": [...]}`` JSON with every key encrypted."""
    return json.dumps({"keys_enc": [encrypt(k) for k in keys]})


def mask_secret(secret: str) -> str:
    """Show only the last 4 characters of a token/API key (never the whole value)."""
    if not secret:
        return ""
    if len(secret) <= 4:
        return "****"
    return f"****{secret[-4:]}"


def last_test_ok(status: str | None) -> bool | None:
    """Outcome of the last connection test, derived from the connection status."""
    return {"connected": True, "error": False}.get(status or "")
