"""Garmin Personal API sync: store the key, pull activities and health data, keep the connection status.

A sync is a background job like an upload import, and its row is part of the same sync log. Activities
are downloaded as their original files and go through the same parse, match and ingest path as uploads.
Health days are built from all endpoints first and stored once per date, because a stored day is replaced
as a whole.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.events import GARMIN_SYNC_STOPPED, EntityCreated, event_bus
from app.core.exceptions import AppError, BadGatewayError, BadRequestError, ConflictError
from app.core.timezone import safe_zone, utc_now
from app.modules.health.contracts import SOURCE_GARMIN, ParsedHealthDay
from app.modules.health.repository import HealthRepository
from app.modules.health.service import HealthService
from app.modules.integrations.garmin import health_mapping
from app.modules.integrations.garmin.archive import ArchiveBudget, ArchiveError, ArchiveLimits, iter_fit_entries
from app.modules.integrations.garmin.connection_config import DISPLAY_NAME, PROVIDER, parse_config, serialize_config
from app.modules.integrations.garmin.import_service import (
    REASON_NOT_SAVED,
    JobOutcome,
    JobStopped,
    Progress,
    process_fit,
    run_job,
    start_background,
    threaded,
)
from app.modules.integrations.garmin.models import JOB_FINISHED, ORIGIN_SYNC, GarminImportJob
from app.modules.integrations.garmin.personal_api import GarminApiError, GarminPersonalApiClient, exchange_key
from app.modules.integrations.garmin.repository import GarminImportRepository
from app.modules.integrations.garmin.schemas import GarminConnectionStatus
from app.modules.integrations.garmin.upload_validation import classify_upload
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import IntegrationUpdate

logger = logging.getLogger(__name__)

FIRST_SYNC_DAYS = 365
OVERLAP_DAYS = 2  # re-read recent days: Garmin fills in the last day or two after the watch syncs
HEALTH_CHUNK_DAYS = 7
RANGE_FIRST = "12m"
RANGE_RECENT = "recent"

REASON_NOT_CONNECTED = "Garmin is not connected"
REASON_KEY_REFUSED = "Garmin refused the key. It may have expired or been deleted; add a new key."
REASON_THROTTLED = "Garmin is limiting requests. The rest will be pulled on the next sync."
REASON_UNREACHABLE = "Could not reach Garmin. The next sync will try again."
REASON_DOWNLOAD = "Could not download this activity from Garmin"
STATUS_SYNCED = "synced"
STATUS_ERROR = "error"
UTC = ZoneInfo("UTC")


def _reason(exc: GarminApiError) -> str:
    if exc.auth:
        return REASON_KEY_REFUSED
    if exc.throttled:
        return REASON_THROTTLED
    return REASON_UNREACHABLE


def _chunks(start: date, end: date, size: int) -> Iterator[tuple[date, date]]:
    while start <= end:
        chunk_end = min(start + timedelta(days=size - 1), end)
        yield start, chunk_end
        start = chunk_end + timedelta(days=1)


def _days(start: date, end: date) -> Iterator[date]:
    while start <= end:
        yield start
        start += timedelta(days=1)


class GarminSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = IntegrationRepository(db)
        self.jobs = GarminImportRepository(db)

    async def get_status(self, user_id: str) -> GarminConnectionStatus:
        conn = await self.repo.get_by_provider(user_id, PROVIDER)
        if conn is None:
            return GarminConnectionStatus(connected=False)
        cfg = parse_config(conn.config_json)
        return GarminConnectionStatus(
            connected=cfg.connected and conn.enabled,
            key_masked=cfg.key_masked,
            status=conn.status,
            last_sync_at=conn.last_sync_at,
            last_sync_message=cfg.last_sync_message,
            last_sync_ok=cfg.last_sync_ok,
            synced_through=cfg.synced_through,
        )

    async def save_key(self, user_id: str, api_key: str) -> GarminConnectionStatus:
        """Check the key with Garmin, then store it encrypted. The key is never returned or logged."""
        key = api_key.strip()
        try:
            await exchange_key(key)
        except GarminApiError as exc:
            logger.warning("Garmin key check failed for user=%s status=%s", user_id, exc.status_code)
            if exc.auth or exc.status_code == 400:
                raise BadRequestError("Garmin did not accept this key. Check it and try again.") from exc
            raise BadGatewayError("Could not reach Garmin. Try again.") from exc
        conn = await self.repo.get_or_create(user_id, PROVIDER, DISPLAY_NAME)
        await self.repo.update(
            conn,
            IntegrationUpdate(
                enabled=True,
                config_json=serialize_config(conn.config_json, api_key=key, last_sync_message=None, last_sync_ok=None),
            ),
        )
        return await self.get_status(user_id)

    async def disconnect(self, user_id: str) -> None:
        """Forget the key. Imported data stays until the user deletes it separately."""
        conn = await self.repo.get_by_provider(user_id, PROVIDER)
        if conn is not None:
            await self.repo.delete(conn)

    async def start_sync(self, user_id: str, factory: async_sessionmaker) -> GarminImportJob:
        """Create a sync job, commit it, and run it in the background."""
        job = await self.create_job(user_id)
        await self.db.commit()  # the background task must be able to see the row
        start_background(run_sync(factory, job.id, user_id), f"garmin-sync-{job.id}")
        return job

    async def create_job(self, user_id: str) -> GarminImportJob:
        conn = await self.repo.get_by_provider(user_id, PROVIDER)
        cfg = parse_config(conn.config_json if conn else None)
        if conn is None or not conn.enabled or not cfg.connected:
            raise BadRequestError("Connect Garmin with a personal API key first")
        if await self.jobs.has_active(user_id):
            raise ConflictError("An import is already running")
        return await self.jobs.create(user_id, RANGE_RECENT if cfg.synced_through else RANGE_FIRST, ORIGIN_SYNC)


async def run_sync(factory: async_sessionmaker, job_id: str, user_id: str) -> JobOutcome:
    """Background entry point for one sync; records the outcome on the connection afterwards."""
    settings = get_settings()
    outcome = await run_job(
        factory,
        job_id,
        user_id,
        lambda db, repo, progress: _sync(db, repo, job_id, user_id, progress, settings),
        label="sync",
    )
    try:
        async with factory() as db:
            await _record_outcome(db, user_id, outcome)
            await db.commit()
    except Exception:
        logger.exception("Could not record the Garmin sync outcome for user=%s", user_id)
    return outcome


async def _user_today(db: AsyncSession, user_id: str) -> date:
    zone = safe_zone(await HealthRepository(db).user_timezone(user_id), UTC)
    return datetime.now(zone).date()


async def _sync(
    db: AsyncSession,
    repo: GarminImportRepository,
    job_id: str,
    user_id: str,
    progress: Progress,
    settings: Settings,
) -> None:
    conn = await IntegrationRepository(db).get_by_provider(user_id, PROVIDER)
    cfg = parse_config(conn.config_json if conn else None)
    if conn is None or not cfg.connected:
        raise JobStopped(REASON_NOT_CONNECTED)
    today = await _user_today(db, user_id)
    start = cfg.synced_through - timedelta(days=OVERLAP_DAYS) if cfg.synced_through else today - timedelta(
        days=FIRST_SYNC_DAYS
    )
    try:
        token = await exchange_key(cfg.api_key)
        async with GarminPersonalApiClient(token) as api:
            await _sync_activities(db, repo, job_id, user_id, api, start, today, progress, settings)
            await _sync_weight(db, user_id, api, start, today)
            await db.commit()
            for chunk_start, chunk_end in _chunks(start, today, HEALTH_CHUNK_DAYS):
                days = await _fetch_health(api, chunk_start, chunk_end)
                await HealthService(db).bulk_upsert_days(user_id, SOURCE_GARMIN, days)
                progress.health_days += len(days)
                await _save_cursor(db, user_id, chunk_end)
                await repo.update_fields(job_id, **progress.as_values())
                await db.commit()
    except GarminApiError as exc:
        logger.warning("Garmin sync stopped for user=%s status=%s", user_id, exc.status_code)
        raise JobStopped(_reason(exc)) from exc


async def _save_cursor(db: AsyncSession, user_id: str, synced_through: date) -> None:
    conn = await IntegrationRepository(db).get_by_provider(user_id, PROVIDER)
    if conn is not None:
        conn.config_json = serialize_config(conn.config_json, synced_through=synced_through)
        await db.flush()


async def _sync_activities(
    db: AsyncSession,
    repo: GarminImportRepository,
    job_id: str,
    user_id: str,
    api: GarminPersonalApiClient,
    start: date,
    end: date,
    progress: Progress,
    settings: Settings,
) -> None:
    limits = ArchiveLimits(
        settings.garmin_import_max_archive_entries,
        settings.garmin_import_max_uncompressed_bytes,
        settings.garmin_import_max_entry_bytes,
    )
    for activity_id in await api.activity_ids(start, end):
        name = f"Garmin activity {activity_id}"
        try:
            data = await api.download_activity(activity_id)
        except GarminApiError as exc:
            if exc.auth or exc.throttled:
                raise
            progress.files_found += 1
            progress.fail(name, REASON_DOWNLOAD)
        else:
            await _ingest_download(db, user_id, name, data, limits, progress, settings)
        await repo.update_fields(job_id, **progress.as_values())
        await db.commit()


async def _ingest_download(
    db: AsyncSession,
    user_id: str,
    name: str,
    data: bytes,
    limits: ArchiveLimits,
    progress: Progress,
    settings: Settings,
) -> None:
    """A download is a zip holding the .FIT file (or, possibly, the bare .FIT file)."""
    try:
        kind = classify_upload(data[:16])
    except AppError:
        progress.files_found += 1
        progress.fail(name, REASON_NOT_SAVED)
        return
    if kind == "fit":
        progress.files_found += 1
        await process_fit(db, user_id, f"{name}.fit", data, None, progress, settings)
        return
    directory = Path(tempfile.mkdtemp(prefix="lifeos-garmin-"))
    try:
        directory.chmod(0o700)
        path = directory / "download.zip"
        path.write_bytes(data)
        async for entry in threaded(iter_fit_entries(path, limits, ArchiveBudget())):
            progress.files_found += 1
            if entry.data is None:
                progress.fail(name, entry.problem or REASON_NOT_SAVED)
            else:
                await process_fit(db, user_id, f"{name}.fit", entry.data, None, progress, settings)
    except ArchiveError as exc:
        progress.fail(name, exc.reason)
    finally:
        shutil.rmtree(directory, ignore_errors=True)


async def _sync_weight(db: AsyncSession, user_id: str, api: GarminPersonalApiClient, start: date, end: date) -> None:
    readings = health_mapping.weight_measurements(await api.weight_range(start, end))
    await HealthService(db).upsert_measurements(user_id, SOURCE_GARMIN, readings)


async def _fetch_health(api: GarminPersonalApiClient, start: date, end: date) -> list[ParsedHealthDay]:
    """Every health value Garmin has for the dates, merged into one day per date."""
    summaries = health_mapping.summary_days(await api.daily_summaries(start, end))
    hrv = health_mapping.hrv_days(await api.daily_hrv(start, end))
    sleep: dict[date, health_mapping.DayValues] = {}
    spo2: dict[date, health_mapping.DayValues] = {}
    for day in _days(start, end):
        sleep[day] = health_mapping.sleep_values(await api.daily_sleep(day))
        spo2[day] = health_mapping.spo2_values(await api.daily_spo2(day))
    return health_mapping.merge_days(summaries, hrv, sleep, spo2)


def _outcome_message(outcome: JobOutcome) -> str:
    if outcome.status != JOB_FINISHED:
        return outcome.error or "The sync stopped unexpectedly"
    p = outcome.progress
    parts = [f"{p.created} new activit{'y' if p.created == 1 else 'ies'}", f"{p.health_days} health days"]
    if p.failed:
        parts.append(f"{p.failed} failed")
    return "Synced " + ", ".join(parts) + "."


async def _record_outcome(db: AsyncSession, user_id: str, outcome: JobOutcome) -> None:
    """Show the result on the connection. A refused key also pauses the daily sync and notifies once."""
    repo = IntegrationRepository(db)
    conn = await repo.get_by_provider(user_id, PROVIDER)
    if conn is None:
        return  # disconnected while the sync was running
    ok = outcome.status == JOB_FINISHED
    key_refused = outcome.error == REASON_KEY_REFUSED
    conn.config_json = serialize_config(
        conn.config_json, last_sync_message=_outcome_message(outcome), last_sync_ok=ok
    )
    conn.status = STATUS_SYNCED if ok else STATUS_ERROR
    if ok:
        conn.last_sync_at = utc_now()
    if key_refused and conn.enabled:
        conn.enabled = False
        await db.flush()
        await event_bus.emit(db, EntityCreated(GARMIN_SYNC_STOPPED, user_id, "", "add a new Garmin key", module="running"))
    await db.flush()


async def sync_all_enabled() -> None:
    """Scheduler entry point: one sync per connected user, one after another."""
    from app.core.database import async_session_factory

    async with async_session_factory() as session:
        conns = await IntegrationRepository(session).list_enabled_by_provider(PROVIDER)
        user_ids = [c.user_id for c in conns]
    for user_id in user_ids:
        try:
            async with async_session_factory() as session:
                job = await GarminSyncService(session).create_job(user_id)
                await session.commit()
                job_id = job.id
        except AppError as exc:
            logger.info("Scheduled Garmin sync skipped for user=%s: %s", user_id, exc)
            continue
        await run_sync(async_session_factory, job_id, user_id)
