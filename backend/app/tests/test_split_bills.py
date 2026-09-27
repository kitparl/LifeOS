"""Split Bills — short links, seats, equal split in paise, pairwise settle, expiry and history.

Pure money logic is tested directly (with Hypothesis for the invariants); everything
that crosses the trust boundary (seat secrets, open/closed links) is tested through the API.
"""

import re
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest
from app.core.timezone import utc_now
from app.modules.finance.split import api as split_api
from app.modules.finance.split.balances import (
    Bill,
    Debt,
    Payment,
    equal_split,
    member_nets,
    pairwise_debts,
    payable,
)
from app.modules.finance.split.codes import SHORT_CODE_ALPHABET
from app.modules.finance.split.models import SplitGroup, SplitHistory
from app.modules.finance.split.upi import build_upi_uri, paise_to_rupees, rupees_to_paise
from hypothesis import given, settings
from hypothesis import strategies as st
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


async def _join(client, code: str, name: str) -> dict:
    resp = await client.post(f"{BASE}/groups/{code}/join", json={"display_name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _bill(client, code: str, secret: str, paid_by: str, member_ids: list[str], rupees, title="Bill"):
    return await client.post(
        f"{BASE}/groups/{code}/expenses",
        json={"title": title, "amount_rupees": rupees, "paid_by": paid_by, "member_ids": member_ids},
        headers=_seat(secret),
    )


async def _group_with(client, *names: str) -> tuple[str, list[dict]]:
    """A group created by names[0] and joined by the rest; returns (code, seats in join order)."""
    created = await _create(client, creator=names[0])
    seats = [created]
    for name in names[1:]:
        seats.append(await _join(client, created["code"], name))
    return created["code"], seats


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


# ======================================================================
# S2 — Join and bills
# ======================================================================

def test_equal_split_three_members():
    assert [share for _, share in equal_split(10000, ["a", "b", "c"])] == [3334, 3333, 3333]


def test_equal_split_seven_members():
    shares = [share for _, share in equal_split(10000, list("abcdefg"))]
    assert shares == [1429, 1429, 1429, 1429, 1428, 1428, 1428]
    assert sum(shares) == 10000


def test_equal_split_single_member_takes_everything():
    assert equal_split(10000, ["payer"]) == [("payer", 10000)]


def test_equal_split_rejects_no_members():
    with pytest.raises(ValueError):
        equal_split(100, [])


member_lists = st.integers(min_value=1, max_value=50).map(lambda n: [f"m{i}" for i in range(n)])
paise_amounts = st.integers(min_value=1, max_value=1_000_000_000)


@given(amount=paise_amounts, members=member_lists)
@settings(deadline=None)
def test_equal_split_invariants(amount, members):
    split = equal_split(amount, members)
    shares = [share for _, share in split]
    assert [member for member, _ in split] == members  # join order kept
    assert sum(shares) == amount
    assert max(shares) - min(shares) <= 1
    remainder = amount % len(members)
    assert shares == sorted(shares, reverse=True)  # extra paise go to the first members
    assert shares.count(amount // len(members) + 1) == remainder or remainder == 0


async def test_join_adds_a_member_and_returns_a_seat(client):
    created = await _create(client)
    joined = await _join(client, created["code"], "Bala")
    assert joined["seat_secret"] and joined["seat_secret"] != created["seat_secret"]
    body = (await client.get(f"{BASE}/groups/{created['code']}", headers=_seat(joined["seat_secret"]))).json()
    assert [m["display_name"] for m in body["members"]] == ["Asha", "Bala"]
    assert body["my_member_id"] == joined["member_id"] and body["is_creator"] is False


async def test_opening_the_link_does_not_add_the_visitor(client):
    created = await _create(client)
    await client.get(f"{BASE}/groups/{created['code']}")
    body = (await client.get(f"{BASE}/groups/{created['code']}")).json()
    assert len(body["members"]) == 1


async def test_join_rejected_when_past_expires_at(client):
    created = await _create(client)
    await _shift_group(client, created["code"], expires_at=utc_now() - timedelta(minutes=1))
    resp = await client.post(f"{BASE}/groups/{created['code']}/join", json={"display_name": "Late"})
    assert resp.status_code == 409
    assert (await client.get(f"{BASE}/groups/{created['code']}")).json()["is_open"] is False


async def test_join_rejected_when_ended(client):
    created = await _create(client)
    await _shift_group(client, created["code"], ended_at=utc_now())
    resp = await client.post(f"{BASE}/groups/{created['code']}/join", json={"display_name": "Late"})
    assert resp.status_code == 409


async def test_join_caps_at_fifty_members(client):
    code, _ = await _group_with(client, "Creator")
    for i in range(49):
        await _join(client, code, f"P{i}")
        if i % 25 == 24:
            split_api.reset_limiters()  # the per-IP join limit is not what this test is about
    resp = await client.post(f"{BASE}/groups/{code}/join", json={"display_name": "One too many"})
    assert resp.status_code == 409


async def test_two_people_on_one_link_each_add_a_bill_and_both_see_both(client):
    code, (asha, bala) = await _group_with(client, "Asha", "Bala")
    ids = [asha["member_id"], bala["member_id"]]
    assert (await _bill(client, code, asha["seat_secret"], asha["member_id"], ids, 600, "Dinner")).status_code == 201
    assert (await _bill(client, code, bala["seat_secret"], bala["member_id"], ids, "99.99", "Cab")).status_code == 201
    for secret in (asha["seat_secret"], bala["seat_secret"]):
        body = (await client.get(f"{BASE}/groups/{code}", headers=_seat(secret))).json()
        assert [e["title"] for e in body["expenses"]] == ["Dinner", "Cab"]
        cab = body["expenses"][1]
        assert cab["amount_paise"] == 9999
        assert [s["amount_paise"] for s in cab["shares"]] == [5000, 4999]  # Asha joined first


async def test_bill_needs_a_seat_secret(client):
    code, (asha,) = await _group_with(client, "Asha")
    ids = [asha["member_id"]]
    missing = await client.post(
        f"{BASE}/groups/{code}/expenses",
        json={"title": "x", "amount_rupees": 10, "paid_by": ids[0], "member_ids": ids},
    )
    assert missing.status_code == 403
    assert (await _bill(client, code, "not-a-seat", ids[0], ids, 10)).status_code == 403


async def test_seat_from_another_group_is_rejected(client):
    code_a, (asha,) = await _group_with(client, "Asha")
    _, (other,) = await _group_with(client, "Other")
    resp = await _bill(client, code_a, other["seat_secret"], asha["member_id"], [asha["member_id"]], 10)
    assert resp.status_code == 403


async def test_bill_validation(client):
    code, (asha, bala) = await _group_with(client, "Asha", "Bala")
    _, (outsider,) = await _group_with(client, "Outsider")
    secret, a, b = asha["seat_secret"], asha["member_id"], bala["member_id"]
    assert (await _bill(client, code, secret, a, [b], 10)).status_code == 400  # payer not included
    assert (await _bill(client, code, secret, a, [a, outsider["member_id"]], 10)).status_code == 400
    assert (await _bill(client, code, secret, a, [], 10)).status_code == 422
    assert (await _bill(client, code, secret, a, [a, a], 10)).status_code == 422
    assert (await _bill(client, code, secret, a, [a], 0)).status_code == 422
    assert (await _bill(client, code, secret, a, [a], "1.234")).status_code == 422


async def test_bill_rejected_after_link_expires(client):
    code, (asha,) = await _group_with(client, "Asha")
    await _shift_group(client, code, expires_at=utc_now() - timedelta(seconds=1))
    resp = await _bill(client, code, asha["seat_secret"], asha["member_id"], [asha["member_id"]], 10)
    assert resp.status_code == 409


async def test_set_and_clear_upi_on_my_seat(client):
    code, (asha,) = await _group_with(client, "Asha")
    url = f"{BASE}/groups/{code}/members/me"
    assert (await client.patch(url, json={"upi_vpa": "asha@okbank"})).status_code == 403
    resp = await client.patch(url, json={"upi_vpa": " Asha.K@OKBank "}, headers=_seat(asha["seat_secret"]))
    assert resp.status_code == 200 and resp.json()["upi_vpa"] == "asha.k@okbank"
    for bad in ("asha", "@bank", "asha@", "a sha@bank", "asha@bank@x"):
        resp = await client.patch(url, json={"upi_vpa": bad}, headers=_seat(asha["seat_secret"]))
        assert resp.status_code == 422, bad
    resp = await client.patch(url, json={"upi_vpa": None}, headers=_seat(asha["seat_secret"]))
    assert resp.json()["upi_vpa"] is None


# ======================================================================
# S3 — Settle
# ======================================================================

def test_paise_to_rupees_formats_two_decimals():
    assert paise_to_rupees(30000) == "300.00"
    assert paise_to_rupees(3334) == "33.34"
    assert paise_to_rupees(5) == "0.05"


def test_build_upi_uri_matches_the_intent_format():
    uri = build_upi_uri("asha@okbank", "Asha K", 30000, "Goa & back")
    assert uri == "upi://pay?pa=asha@okbank&pn=Asha%20K&am=300.00&cu=INR&tn=Goa%20%26%20back"
    with pytest.raises(ValueError):
        build_upi_uri(None, "Asha", 100, "x")


def test_pairwise_debts_net_each_pair_without_simplification():
    # A paid 300 for A,B,C; B paid 90 for A,B,C. B owes A 100-30=70, C owes A 100, C owes B 30.
    bills = [Bill("a", equal_split(30000, ["a", "b", "c"])), Bill("b", equal_split(9000, ["a", "b", "c"]))]
    debts = pairwise_debts(["a", "b", "c"], bills, [])
    assert debts == [Debt("b", "a", 7000), Debt("c", "a", 10000), Debt("c", "b", 3000)]
    confirmed = [Payment("c", "a", 10000)]
    assert pairwise_debts(["a", "b", "c"], bills, confirmed) == [Debt("b", "a", 7000), Debt("c", "b", 3000)]
    assert payable(Debt("b", "a", 7000), [Payment("b", "a", 2000), Payment("c", "a", 500)]) == 5000


@st.composite
def ledgers(draw):
    """A random group: bills with equal splits over included members, plus confirmed payments."""
    members = [f"m{i}" for i in range(draw(st.integers(min_value=1, max_value=8)))]
    bills = []
    for _ in range(draw(st.integers(min_value=0, max_value=6))):
        included = draw(st.lists(st.sampled_from(members), min_size=1, unique=True))
        payer = draw(st.sampled_from(included))
        amount = draw(st.integers(min_value=1, max_value=10_000_000))
        bills.append(Bill(payer, equal_split(amount, [m for m in members if m in included])))
    payments = []
    if len(members) > 1:
        for _ in range(draw(st.integers(min_value=0, max_value=4))):
            payer, payee = draw(st.lists(st.sampled_from(members), min_size=2, max_size=2, unique=True))
            payments.append(Payment(payer, payee, draw(st.integers(min_value=1, max_value=5_000_000))))
    return members, bills, payments


@given(ledger=ledgers())
@settings(deadline=None)
def test_nets_sum_to_zero_and_pairwise_debts_reconcile(ledger):
    members, bills, payments = ledger
    nets = member_nets(members, bills, payments)
    assert sum(nets.values()) == 0
    debts = pairwise_debts(members, bills, payments)
    assert all(d.amount > 0 and d.payer != d.payee for d in debts)
    assert len({frozenset((d.payer, d.payee)) for d in debts}) == len(debts)  # one row per pair
    for m in members:
        received = sum(d.amount for d in debts if d.payee == m)
        owes = sum(d.amount for d in debts if d.payer == m)
        assert received - owes == nets[m]


@given(paise=st.integers(min_value=1, max_value=1_000_000_000))
def test_paise_rupee_round_trip(paise):
    assert rupees_to_paise(Decimal(paise_to_rupees(paise))) == paise
    uri = build_upi_uri("asha@okbank", "Asha", paise, "Dinner")
    assert parse_qs(urlsplit(uri).query)["am"] == [paise_to_rupees(paise)]


async def _balances(client, code: str) -> dict:
    resp = await client.get(f"{BASE}/groups/{code}/balances")
    assert resp.status_code == 200
    return resp.json()


async def _pay(client, code: str, payer_secret: str, payee_id: str, rupees, method="upi"):
    return await client.post(
        f"{BASE}/groups/{code}/settlements",
        json={"payee_member_id": payee_id, "amount_rupees": rupees, "method": method},
        headers=_seat(payer_secret),
    )


async def _confirm(client, settlement_id: str, secret: str | None):
    headers = _seat(secret) if secret else {}
    return await client.post(f"{BASE}/settlements/{settlement_id}/confirm", headers=headers)


async def test_four_members_settle_to_zero_and_a_later_bill_keeps_settlements(client):
    code, seats = await _group_with(client, "Asha", "Bala", "Chen", "Dev")
    asha = seats[0]
    ids = [s["member_id"] for s in seats]
    assert (await _bill(client, code, asha["seat_secret"], asha["member_id"], ids, 400)).status_code == 201

    body = await _balances(client, code)
    assert [n["net_paise"] for n in body["nets"]] == [30000, -10000, -10000, -10000]
    assert [(d["payer_name"], d["payee_name"], d["amount_paise"]) for d in body["debts"]] == [
        ("Bala", "Asha", 10000), ("Chen", "Asha", 10000), ("Dev", "Asha", 10000),
    ]

    for seat in seats[1:]:
        before = (await _balances(client, code))["nets"][0]["net_paise"]
        paid = await _pay(client, code, seat["seat_secret"], asha["member_id"], 100)
        assert paid.status_code == 201 and paid.json()["status"] == "paid"
        # Marked paid only: balances do not move until the payee confirms.
        assert (await _balances(client, code))["nets"][0]["net_paise"] == before
        confirmed = await _confirm(client, paid.json()["id"], asha["seat_secret"])
        assert confirmed.status_code == 200 and confirmed.json()["status"] == "confirmed"

    body = await _balances(client, code)
    assert [n["net_paise"] for n in body["nets"]] == [0, 0, 0, 0]
    assert body["debts"] == []

    bala = seats[1]
    assert (await _bill(client, code, bala["seat_secret"], bala["member_id"], ids, 40)).status_code == 201
    group = (await client.get(f"{BASE}/groups/{code}")).json()
    assert [s["status"] for s in group["settlements"]] == ["confirmed"] * 3
    assert [n["net_paise"] for n in (await _balances(client, code))["nets"]] == [-1000, 3000, -1000, -1000]


async def test_confirm_is_rejected_for_the_payers_secret_and_without_a_seat(client):
    code, (asha, bala) = await _group_with(client, "Asha", "Bala")
    ids = [asha["member_id"], bala["member_id"]]
    await _bill(client, code, asha["seat_secret"], asha["member_id"], ids, 100)
    paid = (await _pay(client, code, bala["seat_secret"], asha["member_id"], 50)).json()
    assert (await _confirm(client, paid["id"], bala["seat_secret"])).status_code == 403
    assert (await _confirm(client, paid["id"], None)).status_code == 403
    assert (await _confirm(client, paid["id"], "not-a-seat")).status_code == 403
    assert (await _confirm(client, "missing", asha["seat_secret"])).status_code == 404


async def test_mark_paid_needs_the_payers_seat_and_a_real_debt(client):
    code, (asha, bala) = await _group_with(client, "Asha", "Bala")
    ids = [asha["member_id"], bala["member_id"]]
    await _bill(client, code, asha["seat_secret"], asha["member_id"], ids, 100)
    no_seat = await client.post(
        f"{BASE}/groups/{code}/settlements",
        json={"payee_member_id": asha["member_id"], "amount_rupees": 50, "method": "cash"},
    )
    assert no_seat.status_code == 403
    # Asha is owed, she owes nobody: nothing to pay.
    assert (await _pay(client, code, asha["seat_secret"], bala["member_id"], 1)).status_code == 400
    assert (await _pay(client, code, bala["seat_secret"], bala["member_id"], 1)).status_code == 400
    assert (await _pay(client, code, bala["seat_secret"], asha["member_id"], "50.01")).status_code == 400
    assert (await _pay(client, code, bala["seat_secret"], asha["member_id"], 20, "card")).status_code == 422


async def test_pending_payment_reduces_the_price_and_blocks_paying_twice(client):
    code, (asha, bala) = await _group_with(client, "Asha", "Bala")
    await client.patch(
        f"{BASE}/groups/{code}/members/me", json={"upi_vpa": "asha@okbank"}, headers=_seat(asha["seat_secret"])
    )
    ids = [asha["member_id"], bala["member_id"]]
    await _bill(client, code, asha["seat_secret"], asha["member_id"], ids, 600)
    assert (await _pay(client, code, bala["seat_secret"], asha["member_id"], 100)).status_code == 201

    debt = (await _balances(client, code))["debts"][0]
    assert (debt["outstanding_paise"], debt["pending_paise"], debt["amount_paise"]) == (30000, 10000, 20000)
    assert debt["amount_rupees"] == "200.00"
    assert "am=200.00" in debt["upi_uri"]
    assert (await _pay(client, code, bala["seat_secret"], asha["member_id"], "200.01")).status_code == 400
    assert (await _pay(client, code, bala["seat_secret"], asha["member_id"], 200)).status_code == 201
    debt = (await _balances(client, code))["debts"][0]
    assert debt["amount_paise"] == 0 and debt["upi_uri"] is None


async def test_debt_has_upi_uri_only_when_the_payee_has_a_vpa(client):
    code, (asha, bala) = await _group_with(client, "Asha K", "Bala")
    ids = [asha["member_id"], bala["member_id"]]
    await _bill(client, code, asha["seat_secret"], asha["member_id"], ids, 600)
    debt = (await _balances(client, code))["debts"][0]
    assert debt["payee_name"] == "Asha K" and debt["upi_uri"] is None
    link = await client.post(
        f"{BASE}/groups/{code}/upi-link",
        json={"payee_member_id": asha["member_id"], "amount_rupees": 300},
        headers=_seat(bala["seat_secret"]),
    )
    assert link.status_code == 400

    await client.patch(
        f"{BASE}/groups/{code}/members/me", json={"upi_vpa": "asha@okbank"}, headers=_seat(asha["seat_secret"])
    )
    debt = (await _balances(client, code))["debts"][0]
    assert debt["upi_uri"].startswith("upi://pay?")
    query = parse_qs(urlsplit(debt["upi_uri"]).query)
    assert query == {"pa": ["asha@okbank"], "pn": ["Asha K"], "am": ["300.00"], "cu": ["INR"], "tn": ["Dinner"]}

    link = await client.post(
        f"{BASE}/groups/{code}/upi-link",
        json={"payee_member_id": asha["member_id"], "amount_rupees": 300},
        headers=_seat(bala["seat_secret"]),
    )
    assert link.status_code == 200 and link.json()["upi_uri"] == debt["upi_uri"]
    no_seat = await client.post(
        f"{BASE}/groups/{code}/upi-link", json={"payee_member_id": asha["member_id"], "amount_rupees": 300}
    )
    assert no_seat.status_code == 403
