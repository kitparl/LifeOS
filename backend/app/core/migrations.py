"""
Idempotent column migration helper.

Since LifeOS uses create_all at startup (no Alembic), new columns added to
SQLAlchemy models require explicit ALTER TABLE statements for existing databases.
This module provides an idempotent helper that safely adds missing columns.
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)

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
    # Q&A: extensible type/category
    ("qa_entries", "type", "VARCHAR(64)"),
    # Integrations: digest bookkeeping for Telegram (and future schedulers)
    ("integration_connections", "last_digest_at", "TIMESTAMP"),
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
