"""Split Bills short codes, seat secrets and link expiry (generic helpers live in `app.core.short_codes`)."""

from datetime import datetime, timedelta
from typing import Literal

from app.core import short_codes

SHORT_CODE_LENGTH = 6
SHORT_CODE_PATTERN = short_codes.code_pattern(SHORT_CODE_LENGTH)

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
    return short_codes.generate_code(SHORT_CODE_LENGTH)


def url_path(code: str) -> str:
    return f"/s/{code}"


def expires_at_for(expiry: Expiry, created_at: datetime) -> datetime:
    return created_at + EXPIRY_DURATIONS[expiry]


def new_seat_secret() -> str:
    return short_codes.new_secret()
