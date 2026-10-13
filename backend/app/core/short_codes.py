"""Unguessable short codes and random secrets for public links (Split Bills, shared trip plans)."""

import hashlib
import secrets

# Omits 0, O, 1 and l so a code read aloud or off a screen is unambiguous.
SHORT_CODE_ALPHABET = "23456789abcdefghijkmnopqrstuvwxyz"


def code_pattern(length: int) -> str:
    return f"^[{SHORT_CODE_ALPHABET}]{{{length}}}$"


def generate_code(length: int) -> str:
    return "".join(secrets.choice(SHORT_CODE_ALPHABET) for _ in range(length))


def new_secret() -> str:
    return secrets.token_urlsafe(24)


def hash_secret(secret: str) -> str:
    """SHA-256 is sufficient: these are 192-bit random tokens, not user-chosen passwords."""
    return hashlib.sha256(secret.encode()).hexdigest()
