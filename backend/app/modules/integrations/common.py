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


def load_api_key(config_json: str | None, *, label: str) -> str:
    """The stored API key from ``{"api_key_enc": ...}``, or "" when missing or undecryptable."""
    data = load_json_object(config_json, label=label)
    try:
        return decrypt(str(data["api_key_enc"])).strip() if data.get("api_key_enc") else ""
    except ValueError:
        logger.warning("Failed to decrypt %s config (tampered or wrong key)", label)
        return ""


def serialize_api_key_config(*, existing_json: str | None, api_key: str | None, label: str) -> str:
    """``{"api_key_enc": ...}`` JSON. A blank/None ``api_key`` keeps the stored key."""
    key_enc = str(load_json_object(existing_json, label=label).get("api_key_enc") or "")
    if api_key is not None and api_key.strip():
        key_enc = encrypt(api_key.strip())
    return json.dumps({"api_key_enc": key_enc})


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
