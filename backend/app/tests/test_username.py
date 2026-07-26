import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.migrations import backfill_usernames, ensure_columns
from app.modules.auth.username_rules import derive_username_from_email, validate_username


@pytest.mark.parametrize(
    "value",
    ["john", "john_smith", "john.smith", "dev123", "a12"],
)
def test_validate_username_accepts(value):
    assert validate_username(value) == value.lower()


@pytest.mark.parametrize(
    "value",
    [
        "123john",
        "john__",
        "john..",
        "john#",
        "john smith",
        "ab",
        "a" * 31,
        "john_",
        "john.",
        "Admin",
        "settings",
    ],
)
def test_validate_username_rejects(value):
    with pytest.raises(ValueError):
        validate_username(value)


def test_validate_username_normalizes_case():
    assert validate_username("John_Smith") == "john_smith"


def test_derive_username_from_email_collision():
    taken = {"john"}
    assert derive_username_from_email("john@example.com", lambda c: c in taken) == "john1"


async def _register(client, *, email, username, display_name="User", password="password123"):
    return await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
            "display_name": display_name,
        },
    )


@pytest.mark.asyncio
async def test_register_requires_username(client):
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "nouser@example.com", "password": "password123", "display_name": "No User"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_rejects_reserved_and_duplicate(client):
    bad = await _register(client, email="a@example.com", username="admin")
    assert bad.status_code == 422

    ok = await _register(client, email="a@example.com", username="alex99", display_name="Alex")
    assert ok.status_code == 201

    dup = await _register(client, email="b@example.com", username="ALEX99")
    assert dup.status_code == 409


@pytest.mark.asyncio
async def test_username_available_endpoint(client):
    await _register(client, email="taken@example.com", username="takenuser")
    free = await client.get("/api/v1/auth/username-available", params={"username": "freeuser"})
    assert free.status_code == 200
    assert free.json()["available"] is True

    taken = await client.get("/api/v1/auth/username-available", params={"username": "TakenUser"})
    assert taken.status_code == 200
    body = taken.json()
    assert body["available"] is False
    assert body["username"] == "takenuser"


@pytest.mark.asyncio
async def test_login_by_username_and_email(client):
    await _register(client, email="login@example.com", username="loginhere", display_name="Login")
    by_user = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "loginhere", "password": "password123"},
    )
    assert by_user.status_code == 200

    by_email = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert by_email.status_code == 200

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {by_user.json()['access_token']}"},
    )
    assert me.json()["username"] == "loginhere"


@pytest.mark.asyncio
async def test_change_username_and_history(client):
    reg = await _register(client, email="chg@example.com", username="oldname", display_name="Changer")
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    changed = await client.patch(
        "/api/v1/auth/me/username",
        headers=headers,
        json={"username": "newname", "reason": "prefer shorter"},
    )
    assert changed.status_code == 200
    assert changed.json()["username"] == "newname"

    hist = await client.get("/api/v1/auth/me/username-history", headers=headers)
    assert hist.status_code == 200
    rows = hist.json()
    assert len(rows) == 1
    assert rows[0]["old_username"] == "oldname"
    assert rows[0]["new_username"] == "newname"
    assert rows[0]["reason"] == "prefer shorter"


@pytest.mark.asyncio
async def test_search_users_privacy_and_matching(client):
    reg = await _register(
        client, email="searchme@example.com", username="john_smith", display_name="John Smith"
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    exact = await client.get("/api/v1/users/search", headers=headers, params={"q": "john_smith"})
    assert exact.status_code == 200
    assert exact.json()[0]["username"] == "john_smith"
    assert set(exact.json()[0].keys()) == {"username", "display_name"}

    partial = await client.get("/api/v1/users/search", headers=headers, params={"q": "JOHN"})
    assert any(u["username"] == "john_smith" for u in partial.json())

    by_name = await client.get("/api/v1/users/search", headers=headers, params={"q": "smith"})
    assert any(u["display_name"] == "John Smith" for u in by_name.json())

    # Non-admin must not match by email
    by_email = await client.get(
        "/api/v1/users/search", headers=headers, params={"q": "searchme@example.com"}
    )
    assert by_email.json() == []


@pytest.mark.asyncio
async def test_backfill_usernames_from_email():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE users (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    display_name VARCHAR(120) NOT NULL DEFAULT '',
                    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC'
                )
                """
            )
        )
        await conn.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, display_name) VALUES "
                "('u1', 'john.doe@example.com', 'x', 'John'), "
                "('u2', 'john.doe@other.com', 'x', 'Jane')"
            )
        )
        await ensure_columns(conn)
        rows = (
            await conn.execute(text("SELECT id, username FROM users ORDER BY id"))
        ).fetchall()
        usernames = {r[0]: r[1] for r in rows}
        assert usernames["u1"] == "john.doe"
        assert usernames["u2"] == "john.doe1"
    await engine.dispose()
