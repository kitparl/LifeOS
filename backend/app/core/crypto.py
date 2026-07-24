"""Symmetric encryption helpers for integration secrets (Fernet).

Uses INTEGRATION_ENC_KEY when set; otherwise derives a stable key from SECRET_KEY.
Never log plaintext secrets. Decrypt fails closed on tamper/invalid ciphertext.
"""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


@lru_cache
def _get_fernet() -> Fernet:
    settings = get_settings()
    key = (settings.integration_enc_key or "").strip()
    if key:
        return Fernet(key.encode() if isinstance(key, str) else key)
    # Derive a stable url-safe 32-byte key from secret_key
    digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(plaintext: str) -> str:
    if plaintext == "":
        return ""
    return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(ciphertext: str) -> str:
    if ciphertext == "":
        return ""
    try:
        return _get_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Invalid or tampered ciphertext") from exc
