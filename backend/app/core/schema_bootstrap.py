"""One-shot schema create/migrate helpers used at startup and by deploy.

With uvicorn ``--workers N`` (N>1), every worker runs the FastAPI lifespan.
Running ``create_all`` / column migrations concurrently against SQLite races
and can leave workers dead so ``/health`` never answers. A cross-process file
lock serialises the work.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import contextmanager
from pathlib import Path

from app.core.database import Base, engine
from app.core.logging_config import configure_logging

logger = logging.getLogger(__name__)

# Always under backend/ (service WorkingDirectory), not beside the DB file —
# production DB paths may be unwritable for creating a sibling lock file.
_LOCK_PATH = Path(__file__).resolve().parents[2] / ".lifeos_schema.lock"


@contextmanager
def _schema_lock():
    """Exclusive flock so only one process mutates schema at a time."""
    import fcntl

    _LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK_PATH.open("w") as lock_file:
        logger.info("Waiting for schema lock (%s)", _LOCK_PATH)
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _import_models() -> None:
    """Register every ORM table on Base.metadata before create_all (the deploy CLI imports nothing else)."""
    import app.modules.ai.models  # noqa: F401
    import app.modules.auth.models  # noqa: F401
    import app.modules.calendar.models  # noqa: F401
    import app.modules.communication.models  # noqa: F401
    import app.modules.communication.vocabulary.models  # noqa: F401
    import app.modules.files.models  # noqa: F401
    import app.modules.files.preview_models  # noqa: F401
    import app.modules.finance.models  # noqa: F401
    import app.modules.habits.models  # noqa: F401
    import app.modules.integrations.github.sync_models  # noqa: F401
    import app.modules.integrations.models  # noqa: F401
    import app.modules.integrations.notifications.outbox_models  # noqa: F401
    import app.modules.integrations.reports.models  # noqa: F401
    import app.modules.journal.models  # noqa: F401
    import app.modules.knowledge_notes.models  # noqa: F401
    import app.modules.memory.models  # noqa: F401
    import app.modules.mood.models  # noqa: F401
    import app.modules.news.models  # noqa: F401
    import app.modules.notifications.models  # noqa: F401
    import app.modules.ocr.models  # noqa: F401
    import app.modules.preferences.models  # noqa: F401
    import app.modules.qa.models  # noqa: F401
    import app.modules.routines.models  # noqa: F401
    import app.modules.running.models  # noqa: F401
    import app.modules.sticky_notes.models  # noqa: F401
    import app.modules.tasks.models  # noqa: F401
    import app.modules.wishlist.models  # noqa: F401


async def apply_schema() -> None:
    """Idempotent create_all + column migrations, under a cross-process lock."""
    from app.core.migrations import ensure_columns

    _import_models()
    with _schema_lock():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await ensure_columns(conn)
        logger.info("Schema bootstrap complete")


def apply_schema_sync() -> None:
    """CLI/deploy entrypoint (blocking)."""
    configure_logging(level=logging.INFO)
    asyncio.run(apply_schema())


if __name__ == "__main__":
    apply_schema_sync()
