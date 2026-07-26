"""
Local → S3/R2 storage backfill.

Usage (from backend/ with venv active):
  python -m app.modules.files.backfill --target s3
  python -m app.modules.files.backfill --target s3 --dry-run
  python -m app.modules.files.backfill --target s3 --delete-local

Idempotent and resumable: skips rows whose target key already exists with a
matching checksum. Local bytes are only removed on an explicit --delete-local pass.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.modules.files.backends import resolve_backend
from app.modules.files.repository import FileRepository

logger = logging.getLogger(__name__)


async def backfill_to(
    db: AsyncSession,
    target_backend: str,
    *,
    dry_run: bool = False,
    delete_local: bool = False,
) -> dict[str, int]:
    settings = get_settings()
    repo = FileRepository(db)
    source = resolve_backend("local", settings)
    target = resolve_backend(target_backend, settings)
    rows = await repo.list_by_storage_backend("local")
    stats = {"copied": 0, "skipped": 0, "failed": 0, "deleted_local": 0}

    for record in rows:
        key = record.storage_key
        try:
            if await target.exists(key):
                if record.checksum_sha256:
                    # Re-verify by hashing target content if possible via open.
                    stream = await target.open(key)
                    digest = hashlib.sha256()
                    async for chunk in stream:
                        digest.update(chunk)
                    if digest.hexdigest() == record.checksum_sha256:
                        if not dry_run:
                            record.storage_backend = target_backend
                            await db.flush()
                        stats["skipped"] += 1
                        if delete_local and not dry_run:
                            await source.delete(key)
                            stats["deleted_local"] += 1
                        continue
                else:
                    stats["skipped"] += 1
                    continue

            if dry_run:
                stats["copied"] += 1
                continue

            stream2 = await source.open(key)
            hasher = hashlib.sha256()

            async def copy_stream():
                async for chunk in stream2:
                    hasher.update(chunk)
                    yield chunk

            await target.save(key, copy_stream(), record.content_type)
            new_sum = hasher.hexdigest()
            if record.checksum_sha256 and new_sum != record.checksum_sha256:
                await target.delete(key)
                raise ValueError(f"Checksum mismatch for {record.id}")
            if not record.checksum_sha256:
                record.checksum_sha256 = new_sum
            record.storage_backend = target_backend
            await db.flush()
            stats["copied"] += 1

            if delete_local:
                await source.delete(key)
                stats["deleted_local"] += 1
        except Exception:
            logger.exception("Backfill failed for file %s", record.id)
            stats["failed"] += 1

    return stats


async def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill local file bytes to S3/R2")
    parser.add_argument("--target", default="s3", choices=["s3"], help="Target storage backend")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--delete-local",
        action="store_true",
        help="After verified copy, remove local bytes (separate opt-in pass)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        try:
            stats = await backfill_to(
                db,
                args.target,
                dry_run=args.dry_run,
                delete_local=args.delete_local,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    logger.info("Backfill complete: %s", stats)
    await engine.dispose()
    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
