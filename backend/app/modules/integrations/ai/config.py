"""Encrypt/decrypt and mask AI provider config stored in IntegrationConnection.config_json.

Shape: {"api_key_enc": str, "default_model": str | null, "base_url": str | null}.
Legacy Sarvam rows ({"api_key_enc": ...} or a plaintext "api_key") parse unchanged.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.core.crypto import decrypt, encrypt

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AiProviderConfig:
    api_key: str
    default_model: str | None = None
    base_url: str | None = None


@dataclass(frozen=True)
class MaskedAiProviderConfig:
    configured: bool
    api_key_masked: str | None
    default_model: str | None
    base_url: str | None


def _mask_key(key: str) -> str:
    if len(key) <= 4:
        return "****"
    return f"****{key[-4:]}"


def _load_json(config_json: str | None) -> dict[str, Any]:
    if not config_json:
        return {}
    try:
        parsed = json.loads(config_json)
    except json.JSONDecodeError:
        logger.warning("Invalid AI provider config_json (not JSON)")
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _optional_str(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def load_config(config_json: str | None) -> AiProviderConfig:
    """Always returns a config; `api_key` is empty when missing or undecryptable."""
    data = _load_json(config_json)
    api_key = ""
    try:
        if data.get("api_key_enc"):
            api_key = decrypt(str(data["api_key_enc"]))
        elif data.get("api_key"):
            api_key = str(data["api_key"])
    except ValueError:
        logger.warning("Failed to decrypt AI provider config (tampered or wrong key)")
    return AiProviderConfig(
        api_key=api_key.strip(),
        default_model=_optional_str(data.get("default_model")),
        base_url=_optional_str(data.get("base_url")),
    )


def parse_config(config_json: str | None) -> AiProviderConfig | None:
    """Config with a usable API key, else None."""
    cfg = load_config(config_json)
    return cfg if cfg.api_key else None


def serialize_config(
    *,
    existing_json: str | None,
    api_key: str | None,
    default_model: str | None,
    base_url: str | None,
) -> str:
    """A blank/None api_key keeps the stored key; default_model/base_url are written as given."""
    existing = _load_json(existing_json)
    key_enc = str(existing.get("api_key_enc") or "")
    if not key_enc and existing.get("api_key"):
        key_enc = encrypt(str(existing["api_key"]))
    if api_key is not None and api_key.strip():
        key_enc = encrypt(api_key.strip())
    return json.dumps(
        {
            "api_key_enc": key_enc,
            "default_model": _optional_str(default_model),
            "base_url": _optional_str(base_url),
        }
    )


def mask_config(config_json: str | None) -> MaskedAiProviderConfig:
    cfg = load_config(config_json)
    return MaskedAiProviderConfig(
        configured=bool(cfg.api_key),
        api_key_masked=_mask_key(cfg.api_key) if cfg.api_key else None,
        default_model=cfg.default_model,
        base_url=cfg.base_url,
    )
