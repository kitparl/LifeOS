import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt
from sqlalchemy import func, select

from app.core.config import get_settings
from app.modules.auth import google_auth
from app.modules.auth.models import User

CLIENT_ID = "test-client.apps.googleusercontent.com"
NOT_FOUND_MSG = "User not found. Please contact your administrator to get access."

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


def _google_token(email: str, **overrides) -> str:
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


@pytest.fixture(autouse=True)
def google_setup(monkeypatch):
    monkeypatch.setattr(get_settings(), "google_client_id", CLIENT_ID)

    async def fake_jwks():
        return _JWKS

    monkeypatch.setattr(google_auth, "_get_google_jwks", fake_jwks)


async def _register(client, email="alice@example.com"):
    r = await client.post("/api/v1/auth/register", json={
        "username": "alice",
        "email": email,
        "password": "password123",
        "display_name": "Alice",
    })
    assert r.status_code == 201


async def _user_count(client) -> int:
    async with client.session_factory() as s:
        return (await s.execute(select(func.count()).select_from(User))).scalar_one()


@pytest.mark.asyncio
async def test_google_login_existing_user(client):
    await _register(client)
    r = await client.post("/api/v1/auth/google", json={"credential": _google_token("Alice@Example.com")})
    assert r.status_code == 200
    assert "refresh_token" in r.cookies
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_google_login_unknown_email_rejected_and_not_created(client):
    await _register(client)
    before = await _user_count(client)
    r = await client.post("/api/v1/auth/google", json={"credential": _google_token("stranger@example.com")})
    assert r.status_code == 401
    assert r.json()["detail"] == NOT_FOUND_MSG
    assert "refresh_token" not in r.cookies
    assert await _user_count(client) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("overrides", [
    {"aud": "someone-else.apps.googleusercontent.com"},
    {"iss": "https://evil.example.com"},
    {"exp": int(time.time()) - 60},
    {"email_verified": False},
])
async def test_google_login_invalid_token_rejected(client, overrides):
    await _register(client)
    r = await client.post("/api/v1/auth/google", json={"credential": _google_token("alice@example.com", **overrides)})
    assert r.status_code == 401
    assert r.json()["detail"] == "Google sign-in failed. Please try again."


@pytest.mark.asyncio
async def test_google_login_garbage_token_rejected(client):
    r = await client.post("/api/v1/auth/google", json={"credential": "not-a-jwt"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Google sign-in failed. Please try again."


@pytest.mark.asyncio
async def test_google_login_not_configured(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "google_client_id", "")
    r = await client.post("/api/v1/auth/google", json={"credential": _google_token("alice@example.com")})
    assert r.status_code == 401
    cfg = await client.get("/api/v1/auth/google/config")
    assert cfg.json() == {"client_id": ""}


@pytest.mark.asyncio
async def test_google_config_returns_client_id(client):
    r = await client.get("/api/v1/auth/google/config")
    assert r.status_code == 200
    assert r.json() == {"client_id": CLIENT_ID}


@pytest.mark.asyncio
async def test_password_login_still_works(client):
    await _register(client)
    r = await client.post("/api/v1/auth/login", json={"identifier": "alice", "password": "password123"})
    assert r.status_code == 200
    assert "refresh_token" in r.cookies
