import json
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, get_or_404
from app.core.timezone import safe_zone, utc_now
from app.modules.health import baselines
from app.modules.health.contracts import SOURCE_MANUAL, ParsedHealthDay, ParsedMeasurement, UpsertCounts
from app.modules.health.metrics import (
    METRIC_BY_KEY,
    METRICS,
    SLEEP_KEYS,
    TODAY_KEYS,
    validate_measurement,
    validate_values,
)
from app.modules.health.models import HealthDay, HealthMeasurement
from app.modules.health.repository import HealthRepository
from app.modules.health.schemas import (
    HealthDayResponse,
    HealthRange,
    HealthTodayResponse,
    MeasurementCreate,
    MeasurementResponse,
    MetricInfo,
    MetricPoint,
    MetricSeriesResponse,
    SleepConsistency,
    SleepResponse,
    TodayMetric,
)

MAX_RANGE_DAYS = 400
LOOKBACK_FOR_TODAY_DAYS = 366
RANGE_DAYS: dict[str, int] = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
ROLLING_DAYS: dict[str, int] = {"7d": 3, "30d": 7, "90d": 7, "1y": 7}
UTC = ZoneInfo("UTC")


def _row_values(row: HealthDay) -> dict[str, int | float | None]:
    return {m.key: getattr(row, m.key) for m in METRICS if getattr(row, m.key) is not None}


class HealthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = HealthRepository(db)

    async def _user_today(self, user_id: str) -> date:
        zone = safe_zone(await self.repo.user_timezone(user_id), UTC)
        return datetime.now(zone).date()

    @staticmethod
    def _merge(rows: list[HealthDay]) -> dict[date, HealthDayResponse]:
        """One merged day per date that has at least one value; a manual value wins field by field."""
        by_date: dict[date, dict[str, dict[str, int | float | None]]] = {}
        for row in rows:
            by_date.setdefault(row.date, {})[row.source] = _row_values(row)
        merged: dict[date, HealthDayResponse] = {}
        for day, by_source in by_date.items():
            values: dict[str, int | float] = {}
            sources: dict[str, str] = {}
            for source, other in sorted(by_source.items()):
                if source != SOURCE_MANUAL:
                    other_values, other_sources = baselines.merge_values(None, other, source)
                    values.update(other_values)
                    sources.update(other_sources)
            manual_values, manual_sources = baselines.merge_values(by_source.get(SOURCE_MANUAL), None, SOURCE_MANUAL)
            values.update(manual_values)
            sources.update(manual_sources)
            if values:
                merged[day] = HealthDayResponse(day=day, values=values, sources=sources)
        return merged

    @staticmethod
    def _check_range(start: date, end: date) -> None:
        if end < start:
            raise BadRequestError("The end date is before the start date")
        if (end - start).days + 1 > MAX_RANGE_DAYS:
            raise BadRequestError(f"Choose at most {MAX_RANGE_DAYS} days")

    @staticmethod
    def metric_catalogue() -> list[MetricInfo]:
        return [
            MetricInfo(
                key=m.key, label=m.label, unit=m.unit, group=m.group, kind=m.kind, min=m.min, max=m.max,
                lower_is_better=m.lower_is_better, today=m.today,
            )
            for m in METRICS
        ]

    # --- Manual entry and reads --------------------------------------------------------------

    async def upsert_manual_day(self, user_id: str, day: date, values: dict[str, object]) -> HealthDayResponse:
        if day > await self._user_today(user_id) + timedelta(days=1):
            raise BadRequestError("The date is in the future")
        clean = validate_values(values)
        row = await self.repo.get_day_row(user_id, day, SOURCE_MANUAL)
        if row is None:
            row = await self.repo.add_day(HealthDay(user_id=user_id, date=day, source=SOURCE_MANUAL))
        for key, value in clean.items():
            setattr(row, key, value)
        await self.repo.save(row)
        merged = self._merge(await self.repo.days_between(user_id, day, day))
        return merged.get(day) or HealthDayResponse(day=day, values={}, sources={})

    async def get_day(self, user_id: str, day: date) -> HealthDayResponse:
        merged = self._merge(await self.repo.days_between(user_id, day, day))
        return get_or_404(merged.get(day), "No health data for this day")

    async def get_days(self, user_id: str, start: date, end: date) -> list[HealthDayResponse]:
        self._check_range(start, end)
        merged = self._merge(await self.repo.days_between(user_id, start, end))
        return [merged[d] for d in sorted(merged)]

    async def get_today(self, user_id: str) -> HealthTodayResponse:
        today = await self._user_today(user_id)
        upper = today + timedelta(days=1)
        merged = self._merge(await self.repo.days_between(user_id, upper - timedelta(days=LOOKBACK_FOR_TODAY_DAYS), upper))
        if not merged:
            return HealthTodayResponse(day=None, is_today=False, metrics=[])
        latest = max(merged)
        metrics = []
        for key in TODAY_KEYS:
            spec = METRIC_BY_KEY[key]
            series = {d: float(m.values[key]) for d, m in merged.items() if key in m.values}
            value = merged[latest].values.get(key)
            avg_7d = baselines.baseline(series, latest, 7, 3)
            avg_30d = baselines.baseline(series, latest, 30, 7)
            marker = baselines.direction(value, avg_30d) if value is not None and avg_30d is not None else None
            metrics.append(
                TodayMetric(
                    key=key, label=spec.label, unit=spec.unit, value=value, avg_7d=avg_7d, avg_30d=avg_30d,
                    marker=marker, favourable=baselines.favourable(marker, spec.lower_is_better),
                    needs_more_data=value is not None and avg_30d is None,
                )
            )
        return HealthTodayResponse(day=latest, is_today=latest == today, metrics=metrics)

    async def get_metric_series(self, user_id: str, key: str, range_: HealthRange) -> MetricSeriesResponse:
        spec = get_or_404(METRIC_BY_KEY.get(key), "Unknown health metric")
        end = await self._user_today(user_id)
        start = end - timedelta(days=RANGE_DAYS[range_] - 1)
        window = ROLLING_DAYS[range_]
        merged = self._merge(await self.repo.days_between(user_id, start - timedelta(days=window - 1), end))
        series = {d: float(m.values[key]) for d, m in merged.items() if key in m.values}
        days = [start + timedelta(days=i) for i in range(RANGE_DAYS[range_])]
        rolling = baselines.rolling_mean(series, days, window)
        in_range = [series[d] for d in days if d in series]
        return MetricSeriesResponse(
            key=key, label=spec.label, unit=spec.unit, range=range_, start=start, end=end,
            points=[MetricPoint(day=d, value=series.get(d)) for d in days],
            rolling=[MetricPoint(day=d, value=v) for d, v in zip(days, rolling, strict=True)],
            average=sum(in_range) / len(in_range) if in_range else None,
            minimum=min(in_range) if in_range else None,
            maximum=max(in_range) if in_range else None,
        )

    async def get_sleep(self, user_id: str, range_: HealthRange) -> SleepResponse:
        end = await self._user_today(user_id)
        start = end - timedelta(days=RANGE_DAYS[range_] - 1)
        merged = self._merge(await self.repo.days_between(user_id, start, end))
        nights = [merged[d] for d in sorted(merged) if any(k in merged[d].values for k in SLEEP_KEYS)]
        beds = [int(n.values["bed_time_min"]) for n in nights if "bed_time_min" in n.values]
        wakes = [int(n.values["wake_time_min"]) for n in nights if "wake_time_min" in n.values]
        return SleepResponse(
            range=range_, start=start, end=end, nights=nights,
            consistency=SleepConsistency(
                nights=len(nights),
                bed_time_sd_min=baselines.clock_spread(beds),
                wake_time_sd_min=baselines.clock_spread(wakes),
            ),
        )

    # --- Measurements ------------------------------------------------------------------------

    @staticmethod
    def _measurement_response(row: HealthMeasurement) -> MeasurementResponse:
        measured = row.measured_at if row.measured_at.tzinfo else row.measured_at.replace(tzinfo=timezone.utc)
        return MeasurementResponse(
            id=row.id, kind=row.kind, measured_at=measured, values=json.loads(row.values_json), source=row.source
        )

    async def add_measurement(self, user_id: str, data: MeasurementCreate) -> MeasurementResponse:
        measured_at = data.measured_at or utc_now()
        if measured_at.tzinfo is None:
            measured_at = measured_at.replace(tzinfo=timezone.utc)
        if measured_at > utc_now() + timedelta(days=1):
            raise BadRequestError("The time is in the future")
        row = await self.repo.add_measurement(
            HealthMeasurement(
                user_id=user_id, measured_at=measured_at, kind=data.kind,
                values_json=json.dumps(data.values), source=SOURCE_MANUAL,
            )
        )
        return self._measurement_response(row)

    async def list_measurements(self, user_id: str, kind: str, start: date, end: date) -> list[MeasurementResponse]:
        self._check_range(start, end)
        lower = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
        upper = datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        rows = await self.repo.list_measurements(user_id, kind, lower, upper)
        return [self._measurement_response(r) for r in rows]

    async def delete_measurement(self, user_id: str, measurement_id: str) -> None:
        row = get_or_404(await self.repo.get_measurement(user_id, measurement_id), "Measurement not found")
        await self.repo.delete_measurement(row)

    # --- Imported data -----------------------------------------------------------------------

    async def bulk_upsert_days(self, user_id: str, source: str, days: list[ParsedHealthDay]) -> UpsertCounts:
        """Replace the rows of an import source, one per date. Never touches other sources; manual is refused."""
        if source == SOURCE_MANUAL:
            raise BadRequestError("Manual data is entered through the health screens")
        created = updated = 0
        for parsed in days:
            clean = validate_values(dict(parsed.values))
            row = await self.repo.get_day_row(user_id, parsed.day, source)
            is_new = row is None
            if row is None:
                row = HealthDay(user_id=user_id, date=parsed.day, source=source)
            for metric in METRICS:
                setattr(row, metric.key, clean.get(metric.key))
            await (self.repo.add_day(row) if is_new else self.repo.save(row))
            created, updated = created + is_new, updated + (not is_new)
        return UpsertCounts(created=created, updated=updated)

    async def upsert_measurements(
        self, user_id: str, source: str, items: list[ParsedMeasurement]
    ) -> UpsertCounts:
        """Insert or update readings from an import source by external id; invalid readings are skipped."""
        if source == SOURCE_MANUAL:
            raise BadRequestError("Manual data is entered through the health screens")
        created = updated = 0
        for item in items:
            try:
                values = validate_measurement(item.kind, dict(item.values))
            except ValueError:
                continue
            values_json = json.dumps(values)
            row = await self.repo.get_measurement_by_external_id(user_id, source, item.external_id)
            if row is None:
                await self.repo.add_measurement(
                    HealthMeasurement(
                        user_id=user_id, measured_at=item.measured_at, kind=item.kind,
                        values_json=values_json, source=source, external_id=item.external_id,
                    )
                )
                created += 1
            elif row.values_json != values_json or row.kind != item.kind:
                row.kind, row.values_json, row.measured_at = item.kind, values_json, item.measured_at
                await self.db.flush()
                updated += 1
        return UpsertCounts(created=created, updated=updated)

    async def count_by_source(self, user_id: str, source: str) -> int:
        return await self.repo.count_days_by_source(user_id, source)

    async def delete_by_source(self, user_id: str, source: str) -> int:
        """Remove everything an import source stored for the user; returns the number of days removed."""
        if source == SOURCE_MANUAL:
            raise BadRequestError("Manual data cannot be removed this way")
        days = await self.repo.delete_days_by_source(user_id, source)
        await self.repo.delete_measurements_by_source(user_id, source)
        return days
