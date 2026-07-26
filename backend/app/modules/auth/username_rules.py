"""Username format rules, reserved list, and backfill helpers.

Pure functions with no app imports so migrations can reuse them.
"""

from __future__ import annotations

import re
from collections.abc import Callable

RESERVED_USERNAMES: frozenset[str] = frozenset(
    {
        "admin",
        "administrator",
        "root",
        "system",
        "support",
        "help",
        "owner",
        "api",
        "bot",
        "telegram",
        "null",
        "undefined",
        "guest",
        "me",
        "settings",
        "profile",
        "login",
        "logout",
        "register",
        "dashboard",
        "task",
        "tasks",
        "notification",
        "notifications",
    }
)

_FORMAT = re.compile(r"^[a-z][a-z0-9._]*[a-z0-9]$")
_INVALID_CHARS = re.compile(r"[^a-z0-9._]")
_CONSECUTIVE = re.compile(r"[._]{2,}")


def normalize_username(raw: str) -> str:
    return (raw or "").strip().lower()


def validate_username(raw: str) -> str:
    """Return normalized username or raise ValueError with a user-facing message."""
    username = normalize_username(raw)
    if not username:
        raise ValueError("Username is required")
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters")
    if len(username) > 30:
        raise ValueError("Username must be at most 30 characters")
    if " " in username:
        raise ValueError("Username cannot contain spaces")
    if not username[0].isalpha():
        raise ValueError("Username must start with a letter")
    if username[-1] in "._":
        raise ValueError("Username cannot end with a period or underscore")
    if _CONSECUTIVE.search(username):
        raise ValueError("Username cannot contain consecutive periods or underscores")
    if not _FORMAT.fullmatch(username):
        raise ValueError("Username may only contain letters, numbers, periods, and underscores")
    if username in RESERVED_USERNAMES:
        raise ValueError("This username is reserved")
    return username


def derive_username_from_email(email: str, is_taken: Callable[[str], bool]) -> str:
    """Sanitize email local part into a unique valid username."""
    local = (email or "").split("@", 1)[0].lower()
    local = _INVALID_CHARS.sub("_", local)
    local = _CONSECUTIVE.sub("_", local).strip("._")
    if not local or not local[0].isalpha():
        local = f"u{local}" if local else "user"
    local = local[:30].rstrip("._")
    while len(local) < 3:
        local = f"{local}x"
    if local in RESERVED_USERNAMES or is_taken(local):
        base = local[:28].rstrip("._") or "user"
        n = 1
        while True:
            candidate = f"{base}{n}"
            if candidate not in RESERVED_USERNAMES and not is_taken(candidate):
                return candidate
            n += 1
            if n > 10_000:
                raise RuntimeError("Could not derive unique username from email")
    return local
