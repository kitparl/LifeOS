import time

import pytest
from app.core.config import get_settings
from app.modules.auth.models import User
from app.tests.google_support import CLIENT_ID
from app.tests.google_support import google_token as _google_token
from sqlalchemy import func, select

NOT_FOUND_MSG = "User not found. Please contact your administrator to get access."


@pytest.fixture(autouse=True)
def google_setup(fake_google_identity):
    """Every test here runs against the local test key."""


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
