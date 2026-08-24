"""Encrypt/decrypt and mask Sarvam integration config stored in config_json."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.core.crypto import decrypt, encrypt

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DecryptedSarvamConfig:
    api_key: str


@dataclass(frozen=True)
class MaskedSarvamConfig:
    configured: bool
    api_key_masked: str | None


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 4:
        return "****"
    return f"****{key[-4:]}"


def _load_json(config_json: str | None) -> dict[str, Any]:
    if not config_json:
        return {}
    try:
        parsed = json.loads(config_json)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def serialize_config(
    *,
    api_key: str | None = None,
    existing_json: str | None = None,
) -> str:
    existing = _load_json(existing_json)
    key_enc = existing.get("api_key_enc") or ""

    if not key_enc and existing.get("api_key"):
        key_enc = encrypt(str(existing["api_key"]))

    if api_key is not None and api_key.strip():
        key_enc = encrypt(api_key.strip())

    return json.dumps({"api_key_enc": key_enc or ""})


def parse_config(config_json: str | None) -> DecryptedSarvamConfig | None:
    data = _load_json(config_json)
    if not data:
        if config_json:
            logger.warning("Invalid sarvam config_json (not JSON)")
        return None

    api_key = ""
    try:
        if data.get("api_key_enc"):
            api_key = decrypt(str(data["api_key_enc"]))
        elif data.get("api_key"):
            api_key = str(data["api_key"])
    except ValueError:
        logger.warning("Failed to decrypt sarvam config (tampered or wrong key)")
        return None

    if not api_key.strip():
        return None
    return DecryptedSarvamConfig(api_key=api_key.strip())


def mask_config(config_json: str | None) -> MaskedSarvamConfig:
    parsed = parse_config(config_json)
    if parsed is None:
        return MaskedSarvamConfig(configured=False, api_key_masked=None)
    return MaskedSarvamConfig(
        configured=True,
        api_key_masked=_mask_key(parsed.api_key),
    )
