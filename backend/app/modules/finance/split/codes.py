"""Short codes, seat secrets and link expiry — the security-sensitive tokens of Split Bills."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Literal

# Omits 0, O, 1 and l so a code read aloud or off a screen is unambiguous.
SHORT_CODE_ALPHABET = "23456789abcdefghijkmnopqrstuvwxyz"
SHORT_CODE_LENGTH = 6
SHORT_CODE_PATTERN = f"^[{SHORT_CODE_ALPHABET}]{{{SHORT_CODE_LENGTH}}}$"

Expiry = Literal["session", "1h", "6h", "24h", "3d", "7d", "30d"]

# `session` stays open until the creator ends it, capped at 12 hours.
EXPIRY_DURATIONS: dict[str, timedelta] = {
    "session": timedelta(hours=12),
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "3d": timedelta(days=3),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def generate_code() -> str:
    return "".join(secrets.choice(SHORT_CODE_ALPHABET) for _ in range(SHORT_CODE_LENGTH))


def url_path(code: str) -> str:
    return f"/s/{code}"


def expires_at_for(expiry: Expiry, created_at: datetime) -> datetime:
    return created_at + EXPIRY_DURATIONS[expiry]


def new_seat_secret() -> str:
    return secrets.token_urlsafe(24)


def hash_secret(secret: str) -> str:
    """SHA-256 is sufficient: seat secrets are 192-bit random tokens, not user-chosen passwords."""
    return hashlib.sha256(secret.encode()).hexdigest()
