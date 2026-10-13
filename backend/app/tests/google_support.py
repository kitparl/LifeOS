"""Signed Google ID tokens for tests: a local RSA key stands in for Google's JWKS."""

from __future__ import annotations

import time

import pytest
from app.core.config import get_settings
from app.modules.auth import google_auth
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt

CLIENT_ID = "test-client.apps.googleusercontent.com"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PRIVATE_PEM = _private_key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
_PUBLIC_PEM = _private_key.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()
_JWKS = {"keys": [{**jwk.construct(_PUBLIC_PEM, "RS256").to_dict(), "kid": "test-kid", "use": "sig"}]}


def google_token(email: str, **overrides) -> str:
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "sub": "1234567890",
        "email": email,
        "email_verified": True,
        "iat": now,
        "exp": now + 600,
        **overrides,
    }
    return jwt.encode(claims, _PRIVATE_PEM, algorithm="RS256", headers={"kid": "test-kid"})


@pytest.fixture
def fake_google_identity(monkeypatch):
    """Configure GOOGLE_CLIENT_ID and serve the test key as Google's JWKS."""
    monkeypatch.setattr(get_settings(), "google_client_id", CLIENT_ID)

    async def fake_jwks():
        return _JWKS

    monkeypatch.setattr(google_auth, "_get_google_jwks", fake_jwks)
