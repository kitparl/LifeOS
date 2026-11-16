import json
import logging
from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, get_or_404
from app.modules.activities.contracts import (
    RUNNING_SPORTS,
    DeleteResult,
    IngestResult,
    OriginalFile,
    ParsedActivity,
)
from app.modules.activities.models import Activity, ActivitySeries
from app.modules.activities.repository import ActivityRepository
from app.modules.activities.schemas import ActivityDetail, ActivitySeriesResponse, LapOut, SplitOut
from app.modules.activities.splits import (
    compute_km_splits,
    decode_polyline,
    downsample_indices,
    encode_polyline,
    pack_series,
    route_points,
    unpack_series,
)
from app.modules.files.service import FileService
from app.modules.files.validation import FIT_MIME
from app.modules.running.contracts import SyncedRunInput
from app.modules.running.service import RunningService

logger = logging.getLogger(__name__)

CHART_SAMPLE_LIMIT = 600
ROUTE_POINT_LIMIT = 1000
STORED_ROUTE_POINT_LIMIT = 2000


def _pick(values: list | None, indices: list[int]) -> list | None:
    return None if values is None else [values[i] for i in indices]


class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ActivityRepository(db)

    async def ingest(self, user_id: str, parsed: ParsedActivity, original: OriginalFile | None = None) -> IngestResult:
        """Store one parsed activity (and its run, for running sports). Idempotent per source and external id.

        Runs inside the caller's transaction: the caller commits on success and rolls back on any exception,
        including the IntegrityError raised when a concurrent import stored the same activity first.
        """
        existing = await self.repo.get_by_external(user_id, parsed.source, parsed.external_id)
        if existing is not None:
            return IngestResult(outcome="duplicate", activity_id=existing.id)

        timezone = await self.repo.user_timezone(user_id)
        splits = compute_km_splits(parsed.series) if parsed.series else []
        points = route_points(parsed.series, STORED_ROUTE_POINT_LIMIT) if parsed.series else []
        activity = Activity(
            user_id=user_id,
            source=parsed.source,
            external_id=parsed.external_id,
            sport=parsed.sport,
            start_time_utc=parsed.start_time_utc,
            timezone=timezone,
            elapsed_seconds=parsed.elapsed_s,
            timer_seconds=parsed.timer_s,
            distance_m=parsed.distance_m,
            elevation_gain_m=parsed.elevation_gain_m,
            avg_hr=parsed.avg_hr,
            max_hr=parsed.max_hr,
            avg_cadence=parsed.avg_cadence,
            max_speed_mps=parsed.max_speed_mps,
            calories=parsed.calories,
            device=parsed.device,
            training_effect_aerobic=parsed.training_effect_aerobic,
            training_effect_anaerobic=parsed.training_effect_anaerobic,
            laps_json=json.dumps([asdict(lap) for lap in parsed.laps]),
            splits_json=json.dumps([asdict(s) for s in splits]),
            polyline=encode_polyline(points) if points else None,
        )
        series = None
        if parsed.series is not None and parsed.series.time_s:
            series = ActivitySeries(data_gz=pack_series(parsed.series), sample_count=len(parsed.series.time_s))
        await self.repo.add(activity, series)

        run_id, run_created, run_matched = None, False, False
        if parsed.sport in RUNNING_SPORTS:
            result = await RunningService(self.db).sync_run_from_activity(
                user_id,
                SyncedRunInput(
                    activity_id=activity.id,
                    source=parsed.source,
                    start_time_utc=parsed.start_time_utc,
                    timezone=timezone,
                    distance_m=parsed.distance_m,
                    timer_seconds=parsed.timer_s,
                    elapsed_seconds=parsed.elapsed_s,
                ),
            )
            run_id, run_created, run_matched = result.run_id, result.created, result.matched_manual

        if original is not None:
            activity.file_id = await self._store_original(user_id, original)
            await self.db.flush()
        return IngestResult("created", activity.id, run_id, run_created, run_matched)

    async def _store_original(self, user_id: str, original: OriginalFile) -> str | None:
        try:
            record = await FileService(self.db).upload(
                user_id,
                original.filename,
                original.data,
                FIT_MIME,
                module="running",
                enforce_rate_limit=False,  # an import is already limited: one job per user, size caps, quota
            )
        except ConflictError:
            logger.warning("Original file already stored; keeping the activity without a second copy")
            return None
        return record.id

    async def get_activity(self, user_id: str, activity_id: str) -> ActivityDetail:
        activity = get_or_404(await self.repo.get(user_id, activity_id), "Activity not found")
        series = await self.repo.get_series(activity.id)
        return ActivityDetail(
            id=activity.id,
            source=activity.source,
            sport=activity.sport,
            start_time_utc=activity.start_time_utc,
            timezone=activity.timezone,
            elapsed_seconds=activity.elapsed_seconds,
            timer_seconds=activity.timer_seconds,
            distance_m=activity.distance_m,
            elevation_gain_m=activity.elevation_gain_m,
            avg_hr=activity.avg_hr,
            max_hr=activity.max_hr,
            avg_cadence=activity.avg_cadence,
            max_speed_mps=activity.max_speed_mps,
            calories=activity.calories,
            device=activity.device,
            training_effect_aerobic=activity.training_effect_aerobic,
            training_effect_anaerobic=activity.training_effect_anaerobic,
            laps=[LapOut(**lap) for lap in json.loads(activity.laps_json or "[]")],
            splits=[SplitOut(**s) for s in json.loads(activity.splits_json or "[]")],
            has_route=bool(activity.polyline),
            has_series=series is not None,
            has_original_file=activity.file_id is not None,
        )

    async def get_series(self, user_id: str, activity_id: str) -> ActivitySeriesResponse:
        activity = get_or_404(await self.repo.get(user_id, activity_id), "Activity not found")
        stored = await self.repo.get_series(activity.id)
        if stored is None:
            raise NotFoundError("This activity has no recorded samples")
        series = unpack_series(stored.data_gz)
        indices = downsample_indices(len(series.time_s), CHART_SAMPLE_LIMIT)
        return ActivitySeriesResponse(
            sample_count=len(series.time_s),
            time_s=[series.time_s[i] for i in indices],
            distance_m=_pick(series.distance_m, indices),
            heart_rate=_pick(series.heart_rate, indices),
            cadence=_pick(series.cadence, indices),
            altitude_m=_pick(series.altitude_m, indices),
            speed_mps=_pick(series.speed_mps, indices),
            route=route_points(series, ROUTE_POINT_LIMIT),
        )

    async def count_by_source(self, user_id: str, source: str) -> int:
        return len(await self.repo.list_by_source(user_id, source))

    async def delete_by_source(self, user_id: str, source: str) -> DeleteResult:
        """Remove every activity of a source and undo what it did to runs and races."""
        activities = await self.repo.list_by_source(user_id, source)
        if not activities:
            return DeleteResult()
        ids = [a.id for a in activities]
        reverted = await RunningService(self.db).revert_runs_for_activities(user_id, ids)
        file_ids = [a.file_id for a in activities if a.file_id]
        await self.repo.delete_many(ids)
        files = FileService(self.db)
        deleted_files = 0
        for file_id in file_ids:
            try:
                await files.delete_file(user_id, file_id)
                deleted_files += 1
            except Exception:  # noqa: BLE001 - leave the file for the existing purge; the data is already gone
                logger.warning("Could not delete a stored original file", exc_info=True)
        return DeleteResult(
            activities_deleted=len(ids),
            runs_deleted=reverted.runs_deleted,
            runs_restored=reverted.runs_restored,
            races_detached=reverted.races_detached,
            files_deleted=deleted_files,
        )


__all__ = ["ActivityService", "decode_polyline"]
