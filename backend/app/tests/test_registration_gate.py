"""Registration gate enforcement tests (no dependency override)."""

import bcrypt
import pytest
from jose import jwt

from app.core.config import get_settings
from app.main import app
from app.modules.auth.registration_gate import (
    REG_UNLOCK_COOKIE,
    require_registration_unlock,
)

GATE_EMAIL = "pranshu.java@gmail.com"
GATE_PASSWORD = "Parley@75220"
GATE_HASH = bcrypt.hashpw(GATE_PASSWORD.encode(), bcrypt.gensalt()).decode()


@pytest.fixture
def gate_settings(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_gate_email", GATE_EMAIL)
    monkeypatch.setattr(settings, "admin_gate_password_hash", GATE_HASH)
    # Module-level settings object used by registration_gate helpers
    import app.modules.auth.registration_gate as gate

    monkeypatch.setattr(gate, "settings", settings)
    yield settings


@pytest.fixture
async def gated_client(client, gate_settings):
    """Same as client but with real registration-unlock enforcement."""
    app.dependency_overrides.pop(require_registration_unlock, None)
    yield client


@pytest.mark.asyncio
async def test_register_locked_without_unlock(gated_client):
    res = await gated_client.post(
        "/api/v1/auth/register",
        json={
            "username": "lockeduser",
            "email": "locked@example.com",
            "password": "password123",
            "display_name": "Locked",
        },
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_gate_login_wrong_credentials(gated_client):
    res = await gated_client.post(
        "/api/v1/auth/registration-gate/login",
        json={"email": GATE_EMAIL, "password": "wrong-password"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_gate_login_wrong_email(gated_client):
    res = await gated_client.post(
        "/api/v1/auth/registration-gate/login",
        json={"email": "other@example.com", "password": GATE_PASSWORD},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_gate_unlock_allows_register_and_create_user(gated_client):
    login = await gated_client.post(
        "/api/v1/auth/registration-gate/login",
        json={"email": GATE_EMAIL, "password": GATE_PASSWORD},
    )
    assert login.status_code == 200
    assert login.json()["ok"] is True
    assert REG_UNLOCK_COOKIE in login.cookies

    status = await gated_client.get("/api/v1/auth/registration-gate/status")
    assert status.status_code == 200
    assert status.json()["unlocked"] is True

    reg = await gated_client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser1",
            "email": "new1@example.com",
            "password": "password123",
            "display_name": "New One",
        },
    )
    assert reg.status_code == 201
    assert "access_token" in reg.json()

    created = await gated_client.post(
        "/api/v1/auth/admin/create-user",
        json={
            "username": "newuser2",
            "email": "new2@example.com",
            "password": "password123",
            "display_name": "New Two",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["email"] == "new2@example.com"
    assert "access_token" not in body
    # Admin create-user must not set a refresh cookie
    assert "refresh_token" not in created.cookies


@pytest.mark.asyncio
async def test_gate_logout_relocks(gated_client):
    await gated_client.post(
        "/api/v1/auth/registration-gate/login",
        json={"email": GATE_EMAIL, "password": GATE_PASSWORD},
    )
    logout = await gated_client.post("/api/v1/auth/registration-gate/logout")
    assert logout.status_code == 200

    status = await gated_client.get("/api/v1/auth/registration-gate/status")
    assert status.json()["unlocked"] is False

    reg = await gated_client.post(
        "/api/v1/auth/register",
        json={
            "username": "afterlock",
            "email": "afterlock@example.com",
            "password": "password123",
            "display_name": "After Lock",
        },
    )
    assert reg.status_code == 401


@pytest.mark.asyncio
async def test_tampered_unlock_token_rejected(gated_client, gate_settings):
    bad = jwt.encode(
        {"sub": "registration-gate", "type": "reg_unlock"},
        "wrong-secret",
        algorithm=gate_settings.algorithm,
    )
    gated_client.cookies.set(REG_UNLOCK_COOKIE, bad)
    reg = await gated_client.post(
        "/api/v1/auth/register",
        json={
            "username": "tampered",
            "email": "tampered@example.com",
            "password": "password123",
            "display_name": "Tampered",
        },
    )
    assert reg.status_code == 401


@pytest.mark.asyncio
async def test_access_token_cannot_masquerade_as_unlock(gated_client, gate_settings):
    """A normal access JWT must not satisfy the registration unlock cookie."""
    from datetime import datetime, timedelta, timezone

    fake = jwt.encode(
        {
            "sub": "some-user-id",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "type": "access",
        },
        gate_settings.secret_key,
        algorithm=gate_settings.algorithm,
    )
    gated_client.cookies.set(REG_UNLOCK_COOKIE, fake)
    reg = await gated_client.post(
        "/api/v1/auth/register",
        json={
            "username": "masquerade",
            "email": "masquerade@example.com",
            "password": "password123",
            "display_name": "Masquerade",
        },
    )
    assert reg.status_code == 401
