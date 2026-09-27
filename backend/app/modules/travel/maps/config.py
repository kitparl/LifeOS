"""Encrypt/decrypt and mask the Google Maps key stored in `IntegrationConnection.config_json`.

Shape: {"api_key_enc": str}. Same pattern as the Wordnik config.
"""

from __future__ import annotations

import json
import logging

from app.core.crypto import decrypt, encrypt
from app.modules.integrations.common import load_json_object, mask_secret

logger = logging.getLogger(__name__)
_LABEL = "google_maps"


def load_api_key(config_json: str | None) -> str:
    """The stored key, or "" when missing or undecryptable."""
    data = load_json_object(config_json, label=_LABEL)
    try:
        return decrypt(str(data["api_key_enc"])).strip() if data.get("api_key_enc") else ""
    except ValueError:
        logger.warning("Failed to decrypt google_maps config (tampered or wrong key)")
        return ""


def serialize_config(*, existing_json: str | None, api_key: str | None) -> str:
    """A blank/None api_key keeps the stored key."""
    existing = load_json_object(existing_json, label=_LABEL)
    key_enc = str(existing.get("api_key_enc") or "")
    if api_key is not None and api_key.strip():
        key_enc = encrypt(api_key.strip())
    return json.dumps({"api_key_enc": key_enc})


def mask_key(api_key: str) -> str | None:
    return mask_secret(api_key) if api_key else None
