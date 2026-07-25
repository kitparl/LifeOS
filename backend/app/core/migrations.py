"""
Idempotent column migration helper.

Since LifeOS uses create_all at startup (no Alembic), new columns added to
SQLAlchemy models require explicit ALTER TABLE statements for existing databases.
This module provides an idempotent helper that safely adds missing columns.
"""

import json
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)

_LEGACY_TELEGRAM_TIMEZONE = "UTC"

# List of (table, column, sql_type) tuples to ensure exist
_COLUMNS_TO_ENSURE: list[tuple[str, str, str]] = [
    # Running: Run.location
    ("runs", "location", "VARCHAR(200)"),
    # Running: RaceEvent extended journal fields
    ("race_events", "organizer", "VARCHAR(200)"),
    ("race_events", "bib_number", "VARCHAR(50)"),
    ("race_events", "finish_time_seconds", "INTEGER"),
    ("race_events", "position", "INTEGER"),
    ("race_events", "medal", "BOOLEAN DEFAULT FALSE"),
    ("race_events", "certificate_url", "TEXT"),
    ("race_events", "event_url", "TEXT"),
    ("race_events", "photos", "TEXT"),  # stored as JSON string
    ("race_events", "attended", "BOOLEAN DEFAULT FALSE"),
    ("race_events", "registered", "BOOLEAN DEFAULT FALSE"),
    # Calendar: reusable scheduling linkage (source module + entity id)
    ("calendar_events", "source_module", "VARCHAR(32)"),
    ("calendar_events", "source_id", "VARCHAR(36)"),
    # Calendar: birthday / immutable event kind
    ("calendar_events", "event_kind", "VARCHAR(16) DEFAULT 'normal'"),
    # Q&A: extensible type/category
    ("qa_entries", "type", "VARCHAR(64)"),
    # Integrations: digest bookkeeping for Telegram (and future schedulers)
    ("integration_connections", "last_digest_at", "TIMESTAMP"),
    # Integrations: per-connection Telegram webhook path secret
    ("integration_connections", "webhook_secret", "VARCHAR(64)"),
    # Integrations: actionable notification keyboards
    ("pending_notifications", "reply_markup_json", "TEXT"),
    # Goals: period types + window
    ("goals", "period", "VARCHAR(16) DEFAULT 'yearly'"),
    ("goals", "period_start", "DATE"),
    ("goals", "period_end", "DATE"),
    # Running: optional shoe name on runs and race events
    ("runs", "shoe", "VARCHAR(80)"),
    ("race_events", "shoe", "VARCHAR(80)"),
    # Routines: period window + skip dates
    ("routines", "start_date", "DATE"),
    ("routines", "end_date", "DATE"),
    ("routines", "skip_dates_json", "TEXT"),
]

_BOOLEAN_DEFAULTS_TO_BACKFILL: list[tuple[str, str]] = [
    ("race_events", "medal"),
    ("race_events", "registered"),
    ("race_events", "attended"),
]


async def ensure_columns(conn: AsyncConnection) -> None:
    """
    Idempotently add new columns to existing tables.
    Silently ignores errors when a column already exists.
    Works with both SQLite and PostgreSQL.
    """
    dialect = conn.dialect.name

    for table, column, col_type in _COLUMNS_TO_ENSURE:
        try:
            if dialect == "postgresql":
                # PostgreSQL: use DO $$ ... EXCEPTION block to avoid errors
                await conn.execute(text(f"""
                    DO $$
                    BEGIN
                        ALTER TABLE {table} ADD COLUMN {column} {col_type};
                    EXCEPTION WHEN duplicate_column THEN
                        NULL;
                    END $$;
                """))
            else:
                # SQLite: ALTER TABLE will raise if column exists; catch it
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
        except Exception as exc:
            # Swallow "duplicate column" / "already exists" errors silently
            msg = str(exc).lower()
            if "duplicate column" in msg or "already exists" in msg or "duplicate" in msg:
                logger.debug("Column %s.%s already exists — skipping", table, column)
            else:
                logger.warning("Could not add column %s.%s: %s", table, column, exc)

    for table, column in _BOOLEAN_DEFAULTS_TO_BACKFILL:
        try:
            await conn.execute(text(f"UPDATE {table} SET {column} = FALSE WHERE {column} IS NULL"))
        except Exception as exc:
            logger.warning("Could not backfill column %s.%s: %s", table, column, exc)

    await backfill_telegram_timezone(conn)


async def backfill_telegram_timezone(conn: AsyncConnection) -> None:
    """
    Rewrite the legacy hardcoded "UTC" timezone on Telegram configs.

    Configs created before scheduled reports persisted timezone="UTC" into
    config_json. Because the key is present, the newer Asia/Kolkata default
    never applies, and the settings page posts the stale value straight back —
    so every cron silently fires at the wrong local time. Each config is
    rewritten at most once (see TZ_BACKFILL_KEY) so a deliberate UTC choice
    made afterwards is preserved.
    """
    from app.modules.integrations.telegram_config import DEFAULT_TIMEZONE, TZ_BACKFILL_KEY

    try:
        rows = (
            await conn.execute(
                text(
                    "SELECT id, config_json FROM integration_connections "
                    "WHERE provider = 'telegram'"
                )
            )
        ).fetchall()
    except Exception as exc:
        logger.warning("Could not read Telegram configs for timezone backfill: %s", exc)
        return

    for row_id, raw in rows:
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or data.get(TZ_BACKFILL_KEY):
            continue

        data[TZ_BACKFILL_KEY] = True
        rewritten = data.get("timezone") == _LEGACY_TELEGRAM_TIMEZONE
        if rewritten:
            data["timezone"] = DEFAULT_TIMEZONE

        try:
            await conn.execute(
                text("UPDATE integration_connections SET config_json = :cfg WHERE id = :id"),
                {"cfg": json.dumps(data), "id": row_id},
            )
        except Exception as exc:
            logger.warning("Could not backfill timezone for connection %s: %s", row_id, exc)
            continue

        if rewritten:
            logger.info(
                "Migrated Telegram connection %s from legacy UTC to %s", row_id, DEFAULT_TIMEZONE
            )
