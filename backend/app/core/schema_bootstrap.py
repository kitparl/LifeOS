"""One-shot schema create/migrate helpers used at startup and by deploy.

With uvicorn ``--workers N`` (N>1), every worker runs the FastAPI lifespan.
Running ``create_all`` / column migrations concurrently against SQLite races
(database locked / duplicate column) and can leave workers dead so ``/health``
never answers. A cross-process file lock serialises the work.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import contextmanager
from pathlib import Path

from app.core.config import get_settings
from app.core.database import Base, engine

logger = logging.getLogger(__name__)


def _lock_path() -> Path:
    settings = get_settings()
    # Prefer a stable path next to the SQLite file when possible; otherwise
    # fall back to the backend working directory.
    url = settings.database_url
    if url.startswith("sqlite"):
        # sqlite+aiosqlite:///./lifeos.db  or  sqlite+aiosqlite:////var/.../lifeos.db
        raw = url.split(":///", 1)[-1]
        db_path = Path(raw)
        if not db_path.is_absolute():
            db_path = Path.cwd() / db_path
        return db_path.parent / ".lifeos_schema.lock"
    return Path.cwd() / ".lifeos_schema.lock"


@contextmanager
def _schema_lock():
    """Exclusive flock so only one process mutates schema at a time."""
    import fcntl

    path = _lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as lock_file:
        logger.info("Waiting for schema lock (%s)", path)
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _import_models() -> None:
    """Register ORM tables on Base.metadata before create_all."""
    import app.modules.auth.models  # noqa: F401
    import app.modules.files.models  # noqa: F401
    import app.modules.ai.models  # noqa: F401
    import app.modules.communication.models  # noqa: F401
    import app.modules.integrations.notifications.outbox_models  # noqa: F401
    import app.modules.integrations.reports.models  # noqa: F401
    import app.modules.integrations.github.sync_models  # noqa: F401
    import app.modules.routines.models  # noqa: F401
    import app.modules.preferences.models  # noqa: F401
    import app.modules.tasks.models  # noqa: F401
    import app.modules.finance.models  # noqa: F401


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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    asyncio.run(apply_schema())


if __name__ == "__main__":
    apply_schema_sync()
