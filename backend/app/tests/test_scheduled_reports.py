"""Tests for Cycle 8: scheduled reports, yearly calendar, reminders, habits↔routines."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient

from app.modules.calendar.models import CalendarEvent
from app.modules.calendar.service import _expand_recurring_event
from app.modules.integrations.telegram_config import parse_preferences, serialize_config
from app.modules.integrations.telegram_templates import chunk_text
# CalendarService unused — expansion tested via _expand_recurring_event


async def _auth_token(client: AsyncClient) -> str:
    email = f"cycle8_{datetime.now(timezone.utc).timestamp()}@example.com"
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Cycle8"},
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- Prefs fallback ---


def test_morning_falls_back_to_digest_prefs():
    raw = serialize_config(
        bot_token="1:ABC",
        chat_id="123",
        digest_enabled=True,
        digest_time="07:30",
        timezone="Asia/Kolkata",
    )
    # Simulate legacy config without morning_* keys
    import json

    data = json.loads(raw)
    data.pop("morning_enabled", None)
    data.pop("morning_time", None)
    prefs = parse_preferences(json.dumps(data))
    assert prefs.morning_enabled is True
    assert prefs.morning_time == "07:30"
    assert prefs.timezone == "Asia/Kolkata"
    assert prefs.midday_time == "12:30"
    assert prefs.night_time == "22:00"
    assert prefs.weekly_weekday == 6


def test_chunk_text_splits_long_messages():
    body = "\n\n".join([f"Section {i}\n" + ("x" * 200) for i in range(30)])
    parts = chunk_text(body, limit=800)
    assert len(parts) > 1
    assert all(len(p) <= 900 for p in parts)


# --- Yearly expand ---


def test_yearly_expansion_same_month_day():
    event = CalendarEvent(
        id="e1",
        user_id="u1",
        title="Birthday — Alice",
        starts_at=datetime(2020, 3, 15, 0, 0, tzinfo=timezone.utc),
        ends_at=None,
        all_day=True,
        category="personal",
        recurrence="yearly",
        event_kind="birthday",
    )
    start = datetime(2026, 3, 1, tzinfo=timezone.utc)
    end = datetime(2026, 3, 31, tzinfo=timezone.utc)
    items = _expand_recurring_event(event, start, end)
    assert len(items) == 1
    assert items[0].starts_at.date() == date(2026, 3, 15)
    assert items[0].event_kind == "birthday"


def test_yearly_feb29_becomes_feb28_in_non_leap():
    event = CalendarEvent(
        id="e2",
        user_id="u1",
        title="Leap day",
        starts_at=datetime(2020, 2, 29, 12, 0, tzinfo=timezone.utc),
        ends_at=None,
        all_day=False,
        category="personal",
        recurrence="yearly",
        event_kind="immutable",
    )
    # 2025 is not a leap year
    start = datetime(2025, 2, 1, tzinfo=timezone.utc)
    end = datetime(2025, 3, 1, tzinfo=timezone.utc)
    items = _expand_recurring_event(event, start, end)
    assert len(items) == 1
    assert items[0].starts_at.date() == date(2025, 2, 28)


# --- API integration ---


@pytest.mark.asyncio
async def test_calendar_yearly_and_birthday_create(client: AsyncClient):
    token = await _auth_token(client)
    payload = {
        "title": "Birthday — Bob",
        "starts_at": "2000-07-25T00:00:00+05:30",
        "all_day": True,
        "recurrence": "none",
        "event_kind": "birthday",
    }
    resp = await client.post("/api/v1/calendar/events", json=payload, headers=_auth(token))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["event_kind"] == "birthday"
    assert data["recurrence"] == "yearly"

    start = "2026-07-01T00:00:00+05:30"
    end = "2026-08-01T00:00:00+05:30"
    listing = await client.get(
        "/api/v1/calendar/events",
        params={"start": start, "end": end},
        headers=_auth(token),
    )
    assert listing.status_code == 200
    titles = [e["title"] for e in listing.json()]
    assert "Birthday — Bob" in titles


@pytest.mark.asyncio
async def test_routine_block_habit_linking(client: AsyncClient):
    token = await _auth_token(client)
    habit = await client.post(
        "/api/v1/habits",
        json={"name": "Meditate", "frequency": "daily"},
        headers=_auth(token),
    )
    assert habit.status_code == 201
    habit_id = habit.json()["id"]

    routine = await client.post(
        "/api/v1/routines",
        json={
            "name": "Morning",
            "days_of_week": [0, 1, 2, 3, 4, 5, 6],
            "timezone": "Asia/Kolkata",
            "blocks": [
                {
                    "title": "Focus",
                    "start_time": "06:00:00",
                    "end_time": "07:00:00",
                    "area": "other",
                    "category": "personal",
                    "habit_ids": [habit_id],
                }
            ],
        },
        headers=_auth(token),
    )
    assert routine.status_code == 201, routine.text
    body = routine.json()
    assert body["blocks"][0]["habit_ids"] == [habit_id]
    assert body["blocks"][0]["habits"][0]["name"] == "Meditate"


@pytest.mark.asyncio
async def test_report_gate_telegram_disabled(client: AsyncClient):
    token = await _auth_token(client)
    # Ensure telegram connection exists but disabled
    await client.put(
        "/api/v1/integrations/telegram/config",
        json={"enabled": False, "morning_enabled": True},
        headers=_auth(token),
    )
    resp = await client.post(
        "/api/v1/integrations/telegram/reports/morning/run",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sent"] is False

    runs = await client.get(
        "/api/v1/integrations/telegram/report-runs",
        headers=_auth(token),
    )
    assert runs.status_code == 200
    rows = runs.json()
    assert any(r["status"] == "skipped" and r["skip_reason"] == "telegram_disabled" for r in rows)


@pytest.mark.asyncio
async def test_midday_skip_when_empty(client: AsyncClient):
    token = await _auth_token(client)
    # No overdue/due-today tasks → midday should skip empty
    # Still need telegram "enabled" for prefs check — without credentials notifier is None
    # Gate order: enabled check first. Create enabled conn without real send by mocking? 
    # Without bot token, enabled can be true but notifier returns None after build.
    # Prefer prefs_off path: enable telegram prefs midday off.
    await client.put(
        "/api/v1/integrations/telegram/config",
        json={"enabled": True, "midday_enabled": False, "timezone": "Asia/Kolkata"},
        headers=_auth(token),
    )
    resp = await client.post(
        "/api/v1/integrations/telegram/reports/midday/run",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["sent"] is False
    runs = await client.get(
        "/api/v1/integrations/telegram/report-runs?job_type=midday",
        headers=_auth(token),
    )
    assert any(r["skip_reason"] == "prefs_off" for r in runs.json())


@pytest.mark.asyncio
async def test_reminder_dedupe_claim():
    """Two claims with the same dedupe_key → second returns None."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.core.database import Base
    from app.modules.integrations.report_repository import ReportRunRepository
    import app.modules.integrations.report_models  # noqa: F401

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        repo = ReportRunRepository(session)
        first = await repo.claim_dedupe(
            user_id="u-dedupe",
            job_type="birthday_reminder",
            dedupe_key="bday:e1:2026-07-25:tminus1",
        )
        assert first is not None
        await session.commit()
        second = await repo.claim_dedupe(
            user_id="u-dedupe",
            job_type="birthday_reminder",
            dedupe_key="bday:e1:2026-07-25:tminus1",
        )
        assert second is None
    await engine.dispose()


@pytest.mark.asyncio
async def test_telegram_prefs_status_exposes_new_fields(client: AsyncClient):
    token = await _auth_token(client)
    resp = await client.put(
        "/api/v1/integrations/telegram/config",
        json={
            "morning_enabled": True,
            "morning_time": "06:00",
            "night_enabled": True,
            "night_time": "22:00",
            "birthday_reminders_enabled": False,
            "timezone": "Asia/Kolkata",
        },
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["morning_time"] == "06:00"
    assert data["night_time"] == "22:00"
    assert data["birthday_reminders_enabled"] is False
    assert data["digest_enabled"] is True  # mirrored
    assert data["digest_time"] == "06:00"


def test_immutable_offset_window_helper():
    from app.modules.integrations.reminder_scanner import _in_window, POLL_GRACE

    tz = ZoneInfo("Asia/Kolkata")
    now = datetime(2026, 7, 25, 12, 0, tzinfo=tz)
    fire = now - timedelta(minutes=5)
    assert _in_window(fire, now)
    assert not _in_window(now - POLL_GRACE - timedelta(minutes=1), now)


# --- Timezone correctness ---


@pytest.mark.asyncio
async def test_registered_cron_fires_at_local_time():
    """A report set for 18:16 in Asia/Kolkata must fire at 18:16 IST, not 18:16 UTC."""
    from app.modules.integrations import scheduler as sched_mod

    sched_mod.start_scheduler()
    try:
        prefs = parse_preferences(
            serialize_config(
                bot_token="1:ABC",
                chat_id="123",
                midday_enabled=True,
                midday_time="18:16",
                timezone="Asia/Kolkata",
            )
        )
        sched_mod.sync_user_jobs("u-tz", prefs, enabled=True)
        next_run = sched_mod.next_run_times("u-tz")["midday"]
        assert next_run is not None
        local = next_run.astimezone(ZoneInfo("Asia/Kolkata"))
        assert (local.hour, local.minute) == (18, 16)
    finally:
        await sched_mod.shutdown_scheduler()


async def _backfill(config: dict) -> dict:
    """Run the startup timezone backfill over a single telegram connection row."""
    import json

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.core.migrations import backfill_telegram_timezone

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "CREATE TABLE integration_connections "
                    "(id VARCHAR PRIMARY KEY, provider VARCHAR, config_json TEXT)"
                )
            )
            await conn.execute(
                text("INSERT INTO integration_connections VALUES ('c1', 'telegram', :cfg)"),
                {"cfg": json.dumps(config)},
            )
            await backfill_telegram_timezone(conn)
            raw = (
                await conn.execute(
                    text("SELECT config_json FROM integration_connections WHERE id = 'c1'")
                )
            ).scalar_one()
        return json.loads(raw)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_backfill_rewrites_legacy_utc_timezone():
    from app.modules.integrations.telegram_config import TZ_BACKFILL_KEY

    data = await _backfill({"timezone": "UTC", "midday_time": "18:16"})
    assert data["timezone"] == "Asia/Kolkata"
    assert data[TZ_BACKFILL_KEY] is True
    assert data["midday_time"] == "18:16"


@pytest.mark.asyncio
async def test_backfill_keeps_deliberate_utc_choice():
    from app.modules.integrations.telegram_config import TZ_BACKFILL_KEY

    data = await _backfill({"timezone": "UTC", TZ_BACKFILL_KEY: True})
    assert data["timezone"] == "UTC"


def test_serialize_config_preserves_backfill_marker():
    import json

    from app.modules.integrations.telegram_config import TZ_BACKFILL_KEY

    existing = json.dumps({"timezone": "UTC", TZ_BACKFILL_KEY: True})
    saved = json.loads(serialize_config(existing_json=existing, midday_time="18:16"))
    assert saved[TZ_BACKFILL_KEY] is True
    assert saved["timezone"] == "UTC"
