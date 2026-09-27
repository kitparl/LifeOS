"""Split Bills — short links, seats, equal split in paise, pairwise settle, expiry and history.

Pure money logic is tested directly (with Hypothesis for the invariants); everything
that crosses the trust boundary (seat secrets, open/closed links) is tested through the API.
"""

import re
from datetime import datetime, timedelta

import pytest
from app.modules.finance.split import api as split_api
from app.modules.finance.split.codes import SHORT_CODE_ALPHABET
from app.modules.finance.split.models import SplitGroup, SplitHistory
from sqlalchemy import select

BASE = "/api/v1/splits"


@pytest.fixture(autouse=True)
def _fresh_limiters():
    split_api.reset_limiters()
    yield
    split_api.reset_limiters()


async def _auth(client, email: str) -> dict[str, str]:
    username = "usr_" + email.split("@")[0].replace(".", "").replace("_", "")[:26]
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "password123", "display_name": "Split"},
    )
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _create(client, name="Dinner", creator="Asha", expiry="24h", headers=None) -> dict:
    resp = await client.post(
        f"{BASE}/groups",
        json={"name": name, "creator_name": creator, "expiry": expiry},
        headers=headers or {},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _seat(secret: str) -> dict[str, str]:
    return {"X-Split-Seat": secret}


async def _history_rows(client) -> list[SplitHistory]:
    async with client.session_factory() as session:
        return list((await session.execute(select(SplitHistory))).scalars().all())


async def _shift_group(client, code: str, **changes) -> None:
    """Move a group's timestamps (simulates the clock passing expiry)."""
    async with client.session_factory() as session:
        group = (await session.execute(select(SplitGroup).where(SplitGroup.code == code))).scalar_one()
        for key, value in changes.items():
            setattr(group, key, value)
        await session.commit()


# ======================================================================
# S1 — Link and group
# ======================================================================

async def test_create_returns_short_code_and_url_path(client):
    created = await _create(client)
    code = created["code"]
    assert len(code) == 6
    assert re.fullmatch(f"[{SHORT_CODE_ALPHABET}]{{6}}", code)
    assert not set(code) & set("0O1l")
    assert created["url_path"] == f"/s/{code}"
    assert created["seat_secret"] and created["member_id"]


@pytest.mark.parametrize(("expiry", "hours"), [("session", 12), ("24h", 24), ("7d", 24 * 7)])
async def test_expiry_presets(client, expiry, hours):
    created = await _create(client, expiry=expiry)
    group = (await client.get(f"{BASE}/groups/{created['code']}")).json()
    span = datetime.fromisoformat(group["expires_at"]) - datetime.fromisoformat(group["created_at"])
    assert span == timedelta(hours=hours)
    assert group["is_open"] is True


async def test_get_group_without_auth_returns_group_members_and_expenses(client):
    created = await _create(client)
    resp = await client.get(f"{BASE}/groups/{created['code']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Dinner"
    assert body["url_path"] == created["url_path"]
    assert [m["display_name"] for m in body["members"]] == ["Asha"]
    assert body["members"][0]["is_creator"] is True
    assert body["expenses"] == [] and body["settlements"] == []
    # Viewer context: an anonymous reader has no seat.
    assert body["my_member_id"] is None and body["is_creator"] is False and body["in_history"] is None


async def test_get_group_with_seat_resolves_viewer(client):
    created = await _create(client)
    body = (await client.get(f"{BASE}/groups/{created['code']}", headers=_seat(created["seat_secret"]))).json()
    assert body["my_member_id"] == created["member_id"]
    assert body["is_creator"] is True


async def test_responses_never_leak_secrets(client):
    created = await _create(client)
    text = (await client.get(f"{BASE}/groups/{created['code']}", headers=_seat(created["seat_secret"]))).text
    assert created["seat_secret"] not in text
    assert "secret_hash" not in text and "user_id" not in text and "email" not in text


async def test_unknown_or_malformed_code(client):
    assert (await client.get(f"{BASE}/groups/zzzzzz")).status_code == 404
    assert (await client.get(f"{BASE}/groups/ABC0l1")).status_code == 422


async def test_create_validates_input(client):
    bad = [
        {"name": "  ", "creator_name": "A", "expiry": "24h"},
        {"name": "x" * 81, "creator_name": "A", "expiry": "24h"},
        {"name": "Trip", "creator_name": "A" * 41, "expiry": "24h"},
        {"name": "Trip", "creator_name": "A", "expiry": "1h"},
    ]
    for body in bad:
        assert (await client.post(f"{BASE}/groups", json=body)).status_code == 422


async def test_guest_create_writes_no_history_logged_in_create_writes_one(client):
    guest = await _create(client)
    assert await _history_rows(client) == []
    headers = await _auth(client, "split.owner@example.com")
    owned = await _create(client, name="Trip", headers=headers)
    rows = await _history_rows(client)
    assert len(rows) == 1
    body = (await client.get(f"{BASE}/groups/{owned['code']}", headers=headers)).json()
    assert body["in_history"] is True
    body = (await client.get(f"{BASE}/groups/{guest['code']}", headers=headers)).json()
    assert body["in_history"] is False


async def test_bad_token_is_401_not_guest(client):
    resp = await client.post(
        f"{BASE}/groups",
        json={"name": "Trip", "creator_name": "A", "expiry": "24h"},
        headers={"Authorization": "Bearer not-a-token"},
    )
    assert resp.status_code == 401


async def test_group_create_is_rate_limited_by_ip(client):
    for _ in range(10):
        await _create(client)
    resp = await client.post(f"{BASE}/groups", json={"name": "x", "creator_name": "y", "expiry": "24h"})
    assert resp.status_code == 429
