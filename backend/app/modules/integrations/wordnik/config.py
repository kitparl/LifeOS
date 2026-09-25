"""Encrypt/decrypt and mask Wordnik config stored in IntegrationConnection.config_json.

Shape: {"api_key_enc": str, "usage": {"remaining": int, "limit": int, "observed_at": iso} | null}.
`usage` is the last rate-limit reading seen on any Wordnik response, so the Word Lab can show
remaining quota without spending a call. Connection-test state lives on the connection row
(`status` / `last_sync_at`), as for AI providers.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.crypto import decrypt, encrypt

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WordnikUsage:
    remaining: int
    limit: int
    observed_at: datetime


@dataclass(frozen=True)
class WordnikConfig:
    api_key: str
    usage: WordnikUsage | None = None


def _load_json(config_json: str | None) -> dict[str, Any]:
    if not config_json:
        return {}
    try:
        parsed = json.loads(config_json)
    except json.JSONDecodeError:
        logger.warning("Invalid wordnik config_json (not JSON)")
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _parse_usage(raw: Any) -> WordnikUsage | None:
    if not isinstance(raw, dict):
        return None
    try:
        return WordnikUsage(
            remaining=int(raw["remaining"]),
            limit=int(raw["limit"]),
            observed_at=datetime.fromisoformat(str(raw["observed_at"])),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _usage_json(usage: WordnikUsage | None) -> dict[str, Any] | None:
    if usage is None:
        return None
    return {"remaining": usage.remaining, "limit": usage.limit, "observed_at": usage.observed_at.isoformat()}


def load_config(config_json: str | None) -> WordnikConfig:
    """Always returns a config; `api_key` is empty when missing or undecryptable."""
    data = _load_json(config_json)
    api_key = ""
    try:
        if data.get("api_key_enc"):
            api_key = decrypt(str(data["api_key_enc"]))
    except ValueError:
        logger.warning("Failed to decrypt wordnik config (tampered or wrong key)")
    return WordnikConfig(api_key=api_key.strip(), usage=_parse_usage(data.get("usage")))


def parse_config(config_json: str | None) -> WordnikConfig | None:
    """Config with a usable API key, else None."""
    cfg = load_config(config_json)
    return cfg if cfg.api_key else None


def serialize_config(*, existing_json: str | None, api_key: str | None) -> str:
    """A blank/None api_key keeps the stored key. A new key clears usage (it belonged to the old key)."""
    existing = _load_json(existing_json)
    key_enc = str(existing.get("api_key_enc") or "")
    usage = existing.get("usage")
    if api_key is not None and api_key.strip():
        key_enc = encrypt(api_key.strip())
        usage = None
    return json.dumps({"api_key_enc": key_enc, "usage": usage})


def with_usage(config_json: str | None, usage: WordnikUsage) -> str:
    data = _load_json(config_json)
    data["usage"] = _usage_json(usage)
    return json.dumps(data)


def mask_key(api_key: str) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 4:
        return "****"
    return f"****{api_key[-4:]}"


def usage_remaining_pct(usage: WordnikUsage | None, now: datetime) -> int | None:
    """Percent of the hourly quota left, or None when unknown.

    Wordnik limits are per clock hour, so a reading from an earlier hour says nothing about now.
    """
    if usage is None or usage.limit <= 0:
        return None
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    if usage.observed_at < hour_start:
        return None
    remaining = max(0, min(usage.remaining, usage.limit))
    return round(remaining / usage.limit * 100)
