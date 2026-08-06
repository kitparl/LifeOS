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
    ("race_events", "skipped", "BOOLEAN DEFAULT FALSE"),
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
    # Wishlist: target year / achieved date / status / priority (replaces cost & progress)
    ("wishlist_items", "target_year", "INTEGER"),
    ("wishlist_items", "achieved_date", "DATE"),
    ("wishlist_items", "status", "VARCHAR(16) DEFAULT 'in_progress'"),
    ("wishlist_items", "priority", "VARCHAR(16) DEFAULT 'medium'"),
    ("wishlist_items", "photos", "TEXT"),  # JSON list of image URLs
    # Auth: public username system (nullable until backfill_usernames)
    ("users", "username", "VARCHAR(30)"),
    ("users", "username_changed_at", "TIMESTAMP"),
    ("users", "username_change_count", "INTEGER DEFAULT 0"),
    ("users", "is_admin", "BOOLEAN DEFAULT FALSE"),
    # Tasks: enterprise soft-delete / archive / optimistic concurrency
    ("tasks", "deleted_at", "TIMESTAMP"),
    ("tasks", "archived_at", "TIMESTAMP"),
    ("tasks", "version", "INTEGER DEFAULT 1"),
    # Files: hardening columns (nullable / defaulted for existing rows)
    ("file_records", "checksum_sha256", "VARCHAR(64)"),
    ("file_records", "extension", "VARCHAR(16)"),
    ("file_records", "visibility", "VARCHAR(16) DEFAULT 'private'"),
    ("file_records", "deleted_at", "TIMESTAMP"),
    ("file_records", "updated_at", "TIMESTAMP"),
]

_BOOLEAN_DEFAULTS_TO_BACKFILL: list[tuple[str, str]] = [
    ("race_events", "medal"),
    ("race_events", "registered"),
    ("race_events", "attended"),
    ("race_events", "skipped"),
    ("users", "is_admin"),
]

_STRING_DEFAULTS_TO_BACKFILL: list[tuple[str, str, str]] = [
    ("wishlist_items", "status", "in_progress"),
    ("wishlist_items", "priority", "medium"),
    ("file_records", "visibility", "private"),
]

# Columns removed from the ORM but still present on older databases.
# Must be dropped (or at least made nullable) or INSERTs omit them and fail NOT NULL.
_COLUMNS_TO_DROP: list[tuple[str, str]] = [
    ("wishlist_items", "cost"),
    ("wishlist_items", "progress"),
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

    for table, column, default in _STRING_DEFAULTS_TO_BACKFILL:
        try:
            await conn.execute(
                text(f"UPDATE {table} SET {column} = :default WHERE {column} IS NULL"),
                {"default": default},
            )
        except Exception as exc:
            logger.warning("Could not backfill column %s.%s: %s", table, column, exc)

    await drop_obsolete_columns(conn, dialect)
    await backfill_telegram_timezone(conn)
    await backfill_usernames(conn)


async def drop_obsolete_columns(conn: AsyncConnection, dialect: str) -> None:
    """Drop columns no longer mapped by SQLAlchemy models (idempotent)."""
    for table, column in _COLUMNS_TO_DROP:
        try:
            if dialect == "postgresql":
                await conn.execute(text(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column}"))
            else:
                # SQLite 3.35+ supports DROP COLUMN
                await conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {column}"))
            logger.info("Dropped obsolete column %s.%s", table, column)
        except Exception as exc:
            msg = str(exc).lower()
            if "no such column" in msg or "does not exist" in msg:
                logger.debug("Column %s.%s already absent — skipping", table, column)
            else:
                # Fallback: at least clear NOT NULL so inserts that omit the column work
                try:
                    if dialect == "postgresql":
                        await conn.execute(
                            text(f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL")
                        )
                        if column == "progress":
                            await conn.execute(
                                text(f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT 0")
                            )
                        logger.warning(
                            "Could not drop %s.%s (%s); made nullable instead",
                            table,
                            column,
                            exc,
                        )
                    else:
                        logger.warning("Could not drop column %s.%s: %s", table, column, exc)
                except Exception as inner:
                    logger.warning(
                        "Could not relax obsolete column %s.%s: %s", table, column, inner
                    )


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


async def backfill_usernames(conn: AsyncConnection) -> None:
    """
    Assign usernames derived from email local parts for existing users.

    Adds a unique index afterward. Safe to re-run: skips rows that already
    have a username.
    """
    from app.modules.auth.username_rules import derive_username_from_email

    try:
        rows = (
            await conn.execute(text("SELECT id, email, username FROM users"))
        ).fetchall()
    except Exception as exc:
        logger.warning("Could not read users for username backfill: %s", exc)
        return

    taken: set[str] = set()
    for _id, _email, username in rows:
        if username:
            taken.add(username.lower())

    for row_id, email, username in rows:
        if username:
            continue
        try:
            derived = derive_username_from_email(
                email or f"user{row_id[:8]}@local",
                lambda candidate, _taken=taken: candidate in _taken,
            )
            taken.add(derived)
            await conn.execute(
                text(
                    "UPDATE users SET username = :username, "
                    "username_change_count = COALESCE(username_change_count, 0) "
                    "WHERE id = :id"
                ),
                {"username": derived, "id": row_id},
            )
            logger.info("Backfilled username %s for user %s", derived, row_id)
        except Exception as exc:
            logger.warning("Could not backfill username for user %s: %s", row_id, exc)

    try:
        await conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)")
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "already exists" in msg or "duplicate" in msg:
            logger.debug("Unique index ix_users_username already exists — skipping")
        else:
            logger.warning("Could not create unique index on users.username: %s", exc)
