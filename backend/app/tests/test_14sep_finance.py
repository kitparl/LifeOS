"""Finance module — generation idempotency, loan/EMI derivation, period filtering.

The pure date logic is tested directly; everything that can drift (duplicate
generation, rewritten history, double-counted EMIs) is tested through the API.
"""

from datetime import date

import pytest
from app.modules.finance.generation import (
    clamp_day,
    emi_schedule,
    period_bounds,
    period_key,
    recurring_due_dates,
)


async def _auth(client, email: str) -> dict[str, str]:
    username = "usr_" + email.split("@")[0].replace(".", "").replace("_", "")[:26]
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "password123", "display_name": "Finance"},
    )
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


# ======================================================================
# Pure schedule arithmetic
# ======================================================================

def test_clamp_day_pulls_back_to_month_end():
    assert clamp_day(2026, 2, 31) == date(2026, 2, 28)
    assert clamp_day(2024, 2, 31) == date(2024, 2, 29)  # leap year
    assert clamp_day(2026, 4, 31) == date(2026, 4, 30)
    assert clamp_day(2026, 1, 15) == date(2026, 1, 15)


def test_recurring_skips_months_before_start_date():
    # Definition starts on the 20th; the 5th of that same month is not back-filled.
    due = recurring_due_dates(date(2026, 1, 20), None, 5, date(2026, 4, 30))
    assert due == [date(2026, 2, 5), date(2026, 3, 5), date(2026, 4, 5)]


def test_recurring_stops_at_end_date():
    due = recurring_due_dates(date(2026, 1, 1), date(2026, 3, 10), 5, date(2026, 12, 31))
    assert due == [date(2026, 1, 5), date(2026, 2, 5), date(2026, 3, 5)]


def test_recurring_day_31_clamps_every_month():
    due = recurring_due_dates(date(2026, 1, 1), None, 31, date(2026, 4, 30))
    assert due == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)]


def test_emi_schedule_walks_the_full_tenure():
    schedule = emi_schedule(date(2026, 2, 5), 5, 36, 15000.0)
    assert len(schedule) == 36
    assert schedule[0] == (1, date(2026, 2, 5), 15000.0)
    assert schedule[1][1] == date(2026, 3, 5)
    assert schedule[-1] == (36, date(2029, 1, 5), 15000.0)


def test_emi_schedule_never_starts_before_emi_start_date():
    # EMI day already passed in the start month -> first EMI rolls forward.
    schedule = emi_schedule(date(2026, 2, 10), 5, 2, 100.0)
    assert schedule[0][1] == date(2026, 3, 5)


def test_period_bounds_defaults_to_current_month():
    assert period_bounds("this_month", date(2026, 9, 14)) == (date(2026, 9, 1), date(2026, 9, 30))
    # December -> January crossing
    assert period_bounds("last_month", date(2026, 1, 5)) == (date(2025, 12, 1), date(2025, 12, 31))
    assert period_bounds("this_year", date(2026, 9, 14)) == (date(2026, 1, 1), date(2026, 12, 31))


def test_period_key_formats_slot():
    assert period_key(date(2026, 9, 5)) == "2026-09"


# ======================================================================
# Recurring generation
# ======================================================================

@pytest.mark.asyncio
async def test_recurring_generation_is_idempotent(client):
    h = await _auth(client, "fin_recurring@example.com")
    today = date.today()
    start = date(today.year - 1, 1, 1)

    created = await client.post(
        "/api/v1/finance/recurring",
        headers=h,
        json={
            "title": "Rent",
            "amount": 25000,
            "expense_kind": "hard",
            "category": "Rent",
            "start_date": start.isoformat(),
            "day_of_month": 5,
        },
    )
    assert created.status_code == 201

    first = await client.get("/api/v1/finance/expenses", headers=h, params={"preset": "this_year"})
    count_after_first = len(first.json())
    assert count_after_first > 0

    # Running generation repeatedly must not create a second Rent for any month.
    for _ in range(3):
        await client.post("/api/v1/finance/recurring/generate", headers=h)

    second = await client.get("/api/v1/finance/expenses", headers=h, params={"preset": "this_year"})
    assert len(second.json()) == count_after_first

    dates = [e["txn_date"] for e in second.json()]
    assert len(dates) == len(set(dates))


@pytest.mark.asyncio
async def test_deactivating_recurring_keeps_history_and_stops_generation(client):
    h = await _auth(client, "fin_deactivate@example.com")
    today = date.today()
    start = date(today.year - 1, 1, 1)

    definition = await client.post(
        "/api/v1/finance/recurring",
        headers=h,
        json={
            "title": "Internet",
            "amount": 1200,
            "expense_kind": "hard",
            "category": "Utilities",
            "start_date": start.isoformat(),
            "day_of_month": 10,
        },
    )
    definition_id = definition.json()["id"]

    before = len(
        (await client.get("/api/v1/finance/expenses", headers=h, params={"preset": "this_year"})).json()
    )
    assert before > 0

    disabled = await client.patch(
        f"/api/v1/finance/recurring/{definition_id}", headers=h, json={"is_active": False}
    )
    assert disabled.json()["is_active"] is False

    await client.post("/api/v1/finance/recurring/generate", headers=h)
    after = len(
        (await client.get("/api/v1/finance/expenses", headers=h, params={"preset": "this_year"})).json()
    )
    # History preserved, nothing new generated.
    assert after == before


@pytest.mark.asyncio
async def test_deleted_generated_expense_is_not_resurrected(client):
    h = await _auth(client, "fin_deleted@example.com")
    today = date.today()

    await client.post(
        "/api/v1/finance/recurring",
        headers=h,
        json={
            "title": "Gym",
            "amount": 2000,
            "expense_kind": "hard",
            "category": "Health",
            "start_date": today.replace(day=1).isoformat(),
            "day_of_month": 1,
        },
    )
    listing = await client.get("/api/v1/finance/expenses", headers=h)
    assert len(listing.json()) == 1
    expense_id = listing.json()[0]["id"]

    assert (await client.delete(f"/api/v1/finance/expenses/{expense_id}", headers=h)).status_code == 204
    await client.post("/api/v1/finance/recurring/generate", headers=h)

    # The (definition, month) slot stays consumed — no silent recreation.
    assert len((await client.get("/api/v1/finance/expenses", headers=h)).json()) == 0


# ======================================================================
# Loans and EMIs
# ======================================================================

async def _create_loan(client, headers, **overrides) -> dict:
    payload = {
        "name": "Personal Loan",
        "lender": "HDFC Bank",
        "principal_amount": 500000,
        "emi_amount": 15000,
        "interest_rate": 11,
        "start_date": "2026-01-05",
        "emi_start_date": "2026-02-05",
        "tenure_months": 36,
        "emi_day": 5,
    }
    payload.update(overrides)
    response = await client.post("/api/v1/finance/loans", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_loan_creation_generates_full_emi_schedule(client):
    h = await _auth(client, "fin_loan@example.com")
    loan = await _create_loan(client, h)

    emis = (await client.get(f"/api/v1/finance/loans/{loan['id']}/emis", headers=h)).json()
    assert len(emis) == 36
    assert emis[0]["emi_number"] == 1
    assert emis[0]["due_date"] == "2026-02-05"
    assert emis[-1]["due_date"] == "2029-01-05"
    assert all(e["amount"] == 15000 for e in emis)


@pytest.mark.asyncio
async def test_loan_counts_are_derived_from_emi_records(client):
    h = await _auth(client, "fin_derived@example.com")
    loan = await _create_loan(client, h)
    emis = (await client.get(f"/api/v1/finance/loans/{loan['id']}/emis", headers=h)).json()

    for emi in emis[:3]:
        paid = await client.post(
            f"/api/v1/finance/loans/{loan['id']}/emis/{emi['id']}/pay", headers=h
        )
        assert paid.status_code == 200
        assert paid.json()["status"] == "PAID"
        assert paid.json()["paid_date"] is not None

    refreshed = (await client.get(f"/api/v1/finance/loans/{loan['id']}", headers=h)).json()
    assert refreshed["emis_total"] == 36
    assert refreshed["emis_paid"] == 3
    assert refreshed["emis_remaining"] == 33
    # Next EMI is the earliest pending one, derived not stored.
    assert refreshed["next_due_date"] == emis[3]["due_date"]


@pytest.mark.asyncio
async def test_emi_becomes_a_hard_expense_exactly_once(client):
    h = await _auth(client, "fin_emi_expense@example.com")
    loan = await _create_loan(client, h)
    emis = (await client.get(f"/api/v1/finance/loans/{loan['id']}/emis", headers=h)).json()

    await client.post(f"/api/v1/finance/loans/{loan['id']}/emis/{emis[0]['id']}/pay", headers=h)

    expenses = (
        await client.get(
            "/api/v1/finance/expenses",
            headers=h,
            params={"preset": "custom", "start": "2026-02-01", "end": "2026-02-28"},
        )
    ).json()
    emi_expenses = [e for e in expenses if e["loan_emi_id"] == emis[0]["id"]]
    assert len(emi_expenses) == 1
    assert emi_expenses[0]["expense_kind"] == "hard"
    assert emi_expenses[0]["category"] == "Loan EMI"
    assert emi_expenses[0]["loan_id"] == loan["id"]

    # Repeated generation must not double-count the same EMI.
    for _ in range(3):
        await client.post("/api/v1/finance/recurring/generate", headers=h)
    expenses_again = (
        await client.get(
            "/api/v1/finance/expenses",
            headers=h,
            params={"preset": "custom", "start": "2026-02-01", "end": "2026-02-28"},
        )
    ).json()
    assert len([e for e in expenses_again if e["loan_emi_id"] == emis[0]["id"]]) == 1


@pytest.mark.asyncio
async def test_editing_emi_amount_leaves_paid_emis_untouched(client):
    h = await _auth(client, "fin_emi_edit@example.com")
    loan = await _create_loan(client, h)
    emis = (await client.get(f"/api/v1/finance/loans/{loan['id']}/emis", headers=h)).json()
    await client.post(f"/api/v1/finance/loans/{loan['id']}/emis/{emis[0]['id']}/pay", headers=h)

    await client.patch(f"/api/v1/finance/loans/{loan['id']}", headers=h, json={"emi_amount": 16000})

    updated = (await client.get(f"/api/v1/finance/loans/{loan['id']}/emis", headers=h)).json()
    paid = next(e for e in updated if e["status"] == "PAID")
    pending = [e for e in updated if e["status"] == "PENDING"]
    assert paid["amount"] == 15000, "paid EMI history must not be rewritten"
    assert all(e["amount"] == 16000 for e in pending)


@pytest.mark.asyncio
async def test_closing_a_loan_cancels_pending_but_preserves_history(client):
    h = await _auth(client, "fin_loan_close@example.com")
    loan = await _create_loan(client, h)
    emis = (await client.get(f"/api/v1/finance/loans/{loan['id']}/emis", headers=h)).json()
    await client.post(f"/api/v1/finance/loans/{loan['id']}/emis/{emis[0]['id']}/pay", headers=h)

    closed = await client.patch(
        f"/api/v1/finance/loans/{loan['id']}", headers=h, json={"status": "CLOSED"}
    )
    assert closed.json()["status"] == "CLOSED"
    assert closed.json()["emis_paid"] == 1
    assert closed.json()["emis_remaining"] == 0

    after = (await client.get(f"/api/v1/finance/loans/{loan['id']}/emis", headers=h)).json()
    assert len(after) == 36, "no EMI record may be deleted"
    assert sum(1 for e in after if e["status"] == "CANCELLED") == 35
    assert sum(1 for e in after if e["status"] == "PAID") == 1


@pytest.mark.asyncio
async def test_loan_summary_reports_monthly_obligation(client):
    h = await _auth(client, "fin_loan_summary@example.com")
    await _create_loan(client, h, name="Loan A", emi_amount=15000)
    await _create_loan(client, h, name="Loan B", emi_amount=17000)

    summary = (await client.get("/api/v1/finance/loans/summary", headers=h)).json()
    assert summary["active_loans"] == 2
    assert summary["monthly_emi_total"] == 32000


# ======================================================================
# Overview, filtering, and the no-savings rule
# ======================================================================

@pytest.mark.asyncio
async def test_overview_splits_soft_and_hard_without_reporting_net(client):
    h = await _auth(client, "fin_overview@example.com")
    today = date.today()

    await client.post(
        "/api/v1/finance/income",
        headers=h,
        json={"title": "Salary", "amount": 100000, "txn_date": today.isoformat(), "category": "Salary"},
    )
    await client.post(
        "/api/v1/finance/expenses",
        headers=h,
        json={"title": "Zepto", "amount": 850, "txn_date": today.isoformat(),
              "expense_kind": "soft", "category": "Groceries"},
    )
    await client.post(
        "/api/v1/finance/expenses",
        headers=h,
        json={"title": "Rent", "amount": 25000, "txn_date": today.isoformat(),
              "expense_kind": "hard", "category": "Rent"},
    )

    overview = (await client.get("/api/v1/finance/overview", headers=h)).json()
    assert overview["total_income"] == 100000
    assert overview["total_expenses"] == 25850
    assert overview["soft_expenses"] == 850
    assert overview["hard_expenses"] == 25000
    assert overview["expense_count"] == 2

    # The module reports activity and obligations — never what is "left".
    for forbidden in ("net", "remaining", "savings", "disposable", "net_worth"):
        assert forbidden not in overview


@pytest.mark.asyncio
async def test_period_filter_scopes_every_figure(client):
    h = await _auth(client, "fin_period@example.com")
    today = date.today()

    await client.post(
        "/api/v1/finance/expenses",
        headers=h,
        json={"title": "This month", "amount": 500, "txn_date": today.isoformat(),
              "expense_kind": "soft", "category": "Food"},
    )
    await client.post(
        "/api/v1/finance/expenses",
        headers=h,
        json={"title": "Old", "amount": 900, "txn_date": "2020-03-15",
              "expense_kind": "soft", "category": "Food"},
    )

    current = (await client.get("/api/v1/finance/overview", headers=h)).json()
    assert current["total_expenses"] == 500

    historical = (
        await client.get(
            "/api/v1/finance/overview",
            headers=h,
            params={"preset": "custom", "start": "2020-01-01", "end": "2020-12-31"},
        )
    ).json()
    assert historical["total_expenses"] == 900
    assert historical["label"] == "2020"  # a whole calendar year collapses to the year


@pytest.mark.asyncio
async def test_breakdown_reports_category_and_kind_totals(client):
    h = await _auth(client, "fin_breakdown@example.com")
    today = date.today()
    for title, amount, kind, category in [
        ("Zepto", 850, "soft", "Food"),
        ("Swiggy", 650, "soft", "Food"),
        ("Rent", 25000, "hard", "Rent"),
    ]:
        await client.post(
            "/api/v1/finance/expenses",
            headers=h,
            json={"title": title, "amount": amount, "txn_date": today.isoformat(),
                  "expense_kind": kind, "category": category},
        )

    breakdown = (await client.get("/api/v1/finance/breakdown", headers=h)).json()
    totals = {row["category"]: row["amount"] for row in breakdown["categories"]}
    assert totals == {"Food": 1500, "Rent": 25000}
    assert breakdown["soft_total"] == 1500
    assert breakdown["hard_total"] == 25000


@pytest.mark.asyncio
async def test_loan_emi_expense_cannot_be_downgraded_to_soft(client):
    h = await _auth(client, "fin_emi_hard@example.com")
    loan = await _create_loan(client, h)
    emis = (await client.get(f"/api/v1/finance/loans/{loan['id']}/emis", headers=h)).json()
    await client.post(f"/api/v1/finance/loans/{loan['id']}/emis/{emis[0]['id']}/pay", headers=h)

    expenses = (
        await client.get(
            "/api/v1/finance/expenses",
            headers=h,
            params={"preset": "custom", "start": "2026-02-01", "end": "2026-02-28"},
        )
    ).json()
    emi_expense = next(e for e in expenses if e["loan_emi_id"])

    rejected = await client.patch(
        f"/api/v1/finance/expenses/{emi_expense['id']}", headers=h, json={"expense_kind": "soft"}
    )
    assert rejected.status_code == 400


@pytest.mark.asyncio
async def test_upcoming_lists_pending_emis_and_recurring(client):
    h = await _auth(client, "fin_upcoming@example.com")
    today = date.today()
    await _create_loan(
        client, h,
        start_date=today.isoformat(),
        emi_start_date=today.isoformat(),
        emi_day=min(today.day + 1, 28) if today.day < 28 else 28,
    )
    await client.post(
        "/api/v1/finance/recurring",
        headers=h,
        json={"title": "Rent", "amount": 25000, "expense_kind": "hard", "category": "Rent",
              "start_date": today.isoformat(),
              "day_of_month": min(today.day + 1, 28) if today.day < 28 else 28},
    )

    upcoming = (await client.get("/api/v1/finance/upcoming", headers=h, params={"days": 60})).json()
    assert len(upcoming) > 0
    assert {item["source"] for item in upcoming} <= {"loan_emi", "recurring"}
    dates = [item["due_date"] for item in upcoming]
    assert dates == sorted(dates)


@pytest.mark.asyncio
async def test_categories_remember_user_created_values(client):
    h = await _auth(client, "fin_categories@example.com")
    defaults = (await client.get("/api/v1/finance/categories", headers=h)).json()
    assert "Rent" in defaults["expense"]
    assert "Salary" in defaults["income"]

    today = date.today()
    await client.post(
        "/api/v1/finance/expenses",
        headers=h,
        json={"title": "Pet food", "amount": 400, "txn_date": today.isoformat(),
              "expense_kind": "soft", "category": "Pets"},
    )
    updated = (await client.get("/api/v1/finance/categories", headers=h)).json()
    assert "Pets" in updated["expense"]


@pytest.mark.asyncio
async def test_legacy_summary_has_no_net_field(client):
    h = await _auth(client, "fin_legacy@example.com")
    await client.post(
        "/api/v1/finance/transactions",
        headers=h,
        json={"txn_type": "expense", "amount": 50, "category": "food", "txn_date": "2026-06-01"},
    )
    summary = (await client.get("/api/v1/finance/summary", headers=h)).json()
    assert summary["total_expenses"] == 50
    assert "net" not in summary
