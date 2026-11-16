"""Garmin import: stage uploads, run the background job, delete imported data.

The job row doubles as the sync log. Progress lives in a plain dataclass and is written with UPDATE
statements, so nothing depends on ORM objects surviving a per-file rollback.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import tempfile
import time
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.events import RUN_SYNCED, RUNS_IMPORTED, EntityCreated, event_bus
from app.core.exceptions import AppError, BadRequestError, ConflictError, PayloadTooLargeError, get_or_404
from app.core.timezone import utc_now
from app.modules.activities.contracts import DeleteResult, OriginalFile, ParsedActivity
from app.modules.activities.service import ActivityService
from app.modules.health.service import HealthService
from app.modules.integrations.garmin.archive import (
    ArchiveBudget,
    ArchiveError,
    ArchiveLimits,
    iter_fit_entries,
)
from app.modules.integrations.garmin.fit_parser import (
    SOURCE,
    FitParseError,
    NotAnActivityError,
    parse_fit,
)
from app.modules.integrations.garmin.models import JOB_FAILED, JOB_FINISHED, JOB_RUNNING, GarminImportJob
from app.modules.integrations.garmin.repository import GarminImportRepository
from app.modules.integrations.garmin.schemas import (
    DeleteImportedResult,
    ImportedSummary,
    ImportFileError,
    ImportJobResponse,
)
from app.modules.integrations.garmin.upload_validation import UploadKind, check_size, classify_upload, max_bytes_for
from app.modules.running.service import RunningService

logger = logging.getLogger(__name__)

MAX_RECORDED_ERRORS = 100
RANGE_12M_DAYS = 365
_CHUNK = 1024 * 1024

REASON_STORAGE_FULL = "Storage limit reached"
REASON_NOT_SAVED = "Could not save activity"
REASON_JOB_FAILED = "The import stopped unexpectedly"

# Strong references to running tasks (a task nobody references can be garbage collected mid-run).
_tasks: set[asyncio.Task] = set()


async def wait_for_imports() -> None:
    """Wait for every running import to finish (used by tests and shutdown)."""
    while _tasks:
        await asyncio.gather(*list(_tasks), return_exceptions=True)


@dataclass(frozen=True)
class StagedFile:
    path: Path
    kind: UploadKind
    name: str


@dataclass
class StagedUploads:
    directory: Path
    files: list[StagedFile]

    def cleanup(self) -> None:
        shutil.rmtree(self.directory, ignore_errors=True)


@dataclass
class Progress:
    files_found: int = 0
    created: int = 0
    duplicates: int = 0
    outside_range: int = 0
    not_activity: int = 0
    failed: int = 0
    runs_created: int = 0
    runs_matched: int = 0
    errors: list[dict[str, str]] = field(default_factory=list)
    new_run_summaries: list[tuple[str, str]] = field(default_factory=list)  # (run id, summary line)

    def fail(self, name: str, reason: str) -> None:
        self.failed += 1
        if len(self.errors) < MAX_RECORDED_ERRORS:
            self.errors.append({"name": name, "reason": reason})

    def as_values(self) -> dict[str, object]:
        return {
            "files_found": self.files_found,
            "created": self.created,
            "duplicates": self.duplicates,
            "outside_range": self.outside_range,
            "not_activity": self.not_activity,
            "failed": self.failed,
            "runs_created": self.runs_created,
            "runs_matched": self.runs_matched,
            "errors_json": json.dumps(self.errors),
        }


def format_run_summary(distance_m: float, timer_s: float) -> str:
    """Like '10.2 km in 52:00 (5:06/km)'."""
    seconds = round(timer_s)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    clock = f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"
    pace = round(timer_s / (distance_m / 1000.0)) if distance_m > 0 else 0
    return f"{distance_m / 1000.0:.1f} km in {clock} ({pace // 60}:{pace % 60:02d}/km)"


def to_response(job: GarminImportJob) -> ImportJobResponse:
    return ImportJobResponse(
        id=job.id,
        status=job.status,
        range_mode=job.range_mode,
        files_found=job.files_found,
        created=job.created,
        duplicates=job.duplicates,
        outside_range=job.outside_range,
        not_activity=job.not_activity,
        failed=job.failed,
        runs_created=job.runs_created,
        runs_matched=job.runs_matched,
        errors=[ImportFileError(**e) for e in json.loads(job.errors_json or "[]")],
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def _clean_name(raw: str | None) -> str:
    base = (raw or "file").replace("\\", "/").rsplit("/", 1)[-1]
    return "".join(ch for ch in base if ch.isprintable())[:80] or "file"


async def stage_uploads(uploads: list[UploadFile], settings: Settings | None = None) -> StagedUploads:
    """Stream uploads to a private temp directory, classifying and size-checking each one.

    Raises (and removes everything it wrote) if any file is unsupported or too large.
    """
    settings = settings or get_settings()
    if not uploads:
        raise BadRequestError("Choose at least one file")
    if len(uploads) > settings.garmin_import_max_files:
        raise BadRequestError(f"Too many files (limit {settings.garmin_import_max_files})")
    directory = Path(tempfile.mkdtemp(prefix="lifeos-import-"))
    directory.chmod(0o700)
    staged = StagedUploads(directory, [])
    try:
        for index, upload in enumerate(uploads):
            head = await upload.read(16)
            kind = classify_upload(head)
            limit = max_bytes_for(kind, settings)
            path = directory / f"upload-{index}"
            total = len(head)
            with path.open("wb") as out:
                out.write(head)
                while chunk := await upload.read(_CHUNK):
                    total += len(chunk)
                    if total > limit:
                        check_size(kind, total, settings)  # raises
                    out.write(chunk)
            check_size(kind, total, settings)
            staged.files.append(StagedFile(path, kind, _clean_name(upload.filename)))
    except BaseException:
        staged.cleanup()
        raise
    return staged


async def _threaded(iterator: Iterator) -> AsyncIterator:
    """Advance a blocking iterator in a worker thread so zip reading never blocks the event loop."""
    sentinel = object()
    while True:
        item = await asyncio.to_thread(next, iterator, sentinel)
        if item is sentinel:
            return
        yield item


class GarminImportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GarminImportRepository(db)

    async def start(
        self, user_id: str, staged: StagedUploads, range_mode: str, factory: async_sessionmaker
    ) -> GarminImportJob:
        """Create the job, commit it, and run it in the background. Cleans up `staged` if it cannot start."""
        try:
            if await self.repo.has_active(user_id):
                raise ConflictError("An import is already running")
            job = await self.repo.create(user_id, range_mode)
            await self.db.commit()  # the background task must be able to see the row
        except BaseException:
            staged.cleanup()
            raise
        task = asyncio.create_task(run_import(factory, job.id, user_id, staged), name=f"garmin-import-{job.id}")
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
        return job

    async def get_job(self, user_id: str, job_id: str) -> ImportJobResponse:
        return to_response(get_or_404(await self.repo.get(user_id, job_id), "Import not found"))

    async def list_jobs(self, user_id: str, limit: int, offset: int) -> tuple[list[ImportJobResponse], int]:
        jobs, total = await self.repo.list_page(user_id, limit, offset)
        return [to_response(j) for j in jobs], total

    async def summary(self, user_id: str) -> ImportedSummary:
        activities = await ActivityService(self.db).count_by_source(user_id, SOURCE)
        created, merged = await RunningService(self.db).count_synced_runs(user_id)
        health_days = await HealthService(self.db).count_by_source(user_id, SOURCE)
        return ImportedSummary(
            activities=activities, runs_created=created, runs_merged_into_manual=merged, health_days=health_days
        )

    async def delete_imported_data(self, user_id: str, include_health: bool = False) -> DeleteImportedResult:
        result: DeleteResult = await ActivityService(self.db).delete_by_source(user_id, SOURCE)
        health_days = await HealthService(self.db).delete_by_source(user_id, SOURCE) if include_health else 0
        return DeleteImportedResult(
            health_days_deleted=health_days,
            activities_deleted=result.activities_deleted,
            runs_deleted=result.runs_deleted,
            runs_restored=result.runs_restored,
            races_detached=result.races_detached,
            files_deleted=result.files_deleted,
        )


async def mark_interrupted_jobs(factory: async_sessionmaker) -> int:
    """At startup: imports that were running when the server stopped cannot continue."""
    async with factory() as db:
        count = await GarminImportRepository(db).mark_interrupted()
        await db.commit()
    if count:
        logger.warning("Marked %s unfinished Garmin import job(s) as interrupted", count)
    return count


async def run_import(factory: async_sessionmaker, job_id: str, user_id: str, staged: StagedUploads) -> None:
    """Background entry point: own session, own failure handling, always cleans up."""
    settings = get_settings()
    progress = Progress()
    started = time.monotonic()
    status, job_error = JOB_FINISHED, None
    try:
        async with factory() as db:
            repo = GarminImportRepository(db)
            await repo.update_fields(job_id, status=JOB_RUNNING, started_at=utc_now())
            await db.commit()
            try:
                await _process_job(db, repo, job_id, user_id, staged, progress, settings)
            except Exception:
                logger.exception("Garmin import job %s failed", job_id)
                await db.rollback()
                status, job_error = JOB_FAILED, REASON_JOB_FAILED
            await repo.update_fields(
                job_id, status=status, error=job_error, finished_at=utc_now(), **progress.as_values()
            )
            await db.commit()
            if status == JOB_FINISHED:
                await _notify(db, user_id, progress)
    except Exception:
        logger.exception("Garmin import job %s could not be finalised", job_id)
    finally:
        staged.cleanup()
        logger.info(
            "Garmin import finished job=%s user=%s status=%s files=%s created=%s duplicates=%s failed=%s seconds=%.1f",
            job_id,
            user_id,
            status,
            progress.files_found,
            progress.created,
            progress.duplicates,
            progress.failed,
            time.monotonic() - started,
        )


async def _process_job(
    db: AsyncSession,
    repo: GarminImportRepository,
    job_id: str,
    user_id: str,
    staged: StagedUploads,
    progress: Progress,
    settings: Settings,
) -> None:
    range_mode = await db.scalar(select(GarminImportJob.range_mode).where(GarminImportJob.id == job_id))
    cutoff = None if range_mode == "all" else utc_now() - timedelta(days=RANGE_12M_DAYS)
    limits = ArchiveLimits(
        settings.garmin_import_max_archive_entries,
        settings.garmin_import_max_uncompressed_bytes,
        settings.garmin_import_max_entry_bytes,
    )

    async def handle(name: str, data: bytes | None, problem: str | None = None) -> None:
        progress.files_found += 1
        if data is None:
            progress.fail(name, problem or REASON_NOT_SAVED)
        else:
            await _process_fit(db, user_id, name, data, cutoff, progress, settings)
        await repo.update_fields(job_id, **progress.as_values())
        await db.commit()

    for item in staged.files:
        if item.kind == "fit":
            await handle(item.name, item.path.read_bytes())
            continue
        try:
            entries = iter_fit_entries(item.path, limits, ArchiveBudget())
            async for entry in _threaded(entries):
                await handle(entry.name, entry.data, entry.problem)
        except ArchiveError as exc:
            progress.fail(item.name, exc.reason)
            await repo.update_fields(job_id, **progress.as_values())
            await db.commit()


async def _process_fit(
    db: AsyncSession,
    user_id: str,
    name: str,
    data: bytes,
    cutoff: datetime | None,
    progress: Progress,
    settings: Settings,
) -> None:
    try:
        parsed: ParsedActivity = await asyncio.to_thread(
            parse_fit, data, max_messages=settings.fit_parse_max_messages, max_seconds=settings.fit_parse_max_seconds
        )
    except NotAnActivityError:
        progress.not_activity += 1
        return
    except FitParseError as exc:
        progress.fail(name, exc.reason)
        return
    if cutoff is not None and parsed.start_time_utc < cutoff:
        progress.outside_range += 1
        return
    try:
        result = await ActivityService(db).ingest(user_id, parsed, OriginalFile(name, data))
        await db.commit()
    except IntegrityError:  # the same activity was stored first by something else
        await db.rollback()
        progress.duplicates += 1
        return
    except PayloadTooLargeError:
        await db.rollback()
        progress.fail(name, REASON_STORAGE_FULL)
        return
    except AppError:
        await db.rollback()
        logger.warning("Import of one file was refused", exc_info=True)
        progress.fail(name, REASON_NOT_SAVED)
        return
    except Exception:
        await db.rollback()
        logger.exception("Import of one file failed")
        progress.fail(name, REASON_NOT_SAVED)
        return
    if result.outcome == "duplicate":
        progress.duplicates += 1
        return
    progress.created += 1
    if result.run_created and result.run_id:
        progress.runs_created += 1
        progress.new_run_summaries.append((result.run_id, format_run_summary(parsed.distance_m, parsed.timer_s)))
    elif result.run_matched:
        progress.runs_matched += 1


async def _notify(db: AsyncSession, user_id: str, progress: Progress) -> None:
    """One message per import: the run itself when exactly one was created, a count when several were."""
    created = progress.runs_created
    if created == 0:
        return
    try:
        if created == 1 and progress.new_run_summaries:
            run_id, line = progress.new_run_summaries[0]
            event = EntityCreated(RUN_SYNCED, user_id, run_id, line, module="running")
        else:
            event = EntityCreated(RUNS_IMPORTED, user_id, "", f"{created} runs", module="running")
        await event_bus.emit(db, event)
        await db.commit()
    except Exception:
        logger.exception("Could not send the import notification")
        await db.rollback()
