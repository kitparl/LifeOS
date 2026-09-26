"""Helpers shared by the per-provider integration configs (AI, Wordnik, GitHub, Google Calendar, Telegram)."""

from __future__ import annotations

import json
import logging
from typing import Any

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
