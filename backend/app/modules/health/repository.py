from datetime import date, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.health.models import HealthDay, HealthMeasurement


class HealthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def user_timezone(self, user_id: str) -> str | None:
        return await self.db.scalar(select(User.timezone).where(User.id == user_id))

    async def days_between(self, user_id: str, start: date, end: date) -> list[HealthDay]:
        result = await self.db.execute(
            select(HealthDay).where(HealthDay.user_id == user_id, HealthDay.date >= start, HealthDay.date <= end)
        )
        return list(result.scalars().all())

    async def get_day_row(self, user_id: str, day: date, source: str) -> HealthDay | None:
        result = await self.db.execute(
            select(HealthDay).where(HealthDay.user_id == user_id, HealthDay.date == day, HealthDay.source == source)
        )
        return result.scalar_one_or_none()

    async def add_day(self, row: HealthDay) -> HealthDay:
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def save(self, row: HealthDay) -> HealthDay:
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def count_days_by_source(self, user_id: str, source: str) -> int:
        return (
            await self.db.scalar(
                select(func.count()).select_from(HealthDay).where(HealthDay.user_id == user_id, HealthDay.source == source)
            )
        ) or 0

    async def delete_days_by_source(self, user_id: str, source: str) -> int:
        result = await self.db.execute(delete(HealthDay).where(HealthDay.user_id == user_id, HealthDay.source == source))
        return result.rowcount or 0

    async def add_measurement(self, row: HealthMeasurement) -> HealthMeasurement:
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def list_measurements(
        self, user_id: str, kind: str, start: datetime, end: datetime
    ) -> list[HealthMeasurement]:
        result = await self.db.execute(
            select(HealthMeasurement)
            .where(
                HealthMeasurement.user_id == user_id,
                HealthMeasurement.kind == kind,
                HealthMeasurement.measured_at >= start,
                HealthMeasurement.measured_at <= end,
            )
            .order_by(HealthMeasurement.measured_at.desc())
        )
        return list(result.scalars().all())

    async def get_measurement(self, user_id: str, measurement_id: str) -> HealthMeasurement | None:
        result = await self.db.execute(
            select(HealthMeasurement).where(
                HealthMeasurement.id == measurement_id, HealthMeasurement.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def delete_measurement(self, row: HealthMeasurement) -> None:
        await self.db.delete(row)
        await self.db.flush()

    async def delete_measurements_by_source(self, user_id: str, source: str) -> int:
        result = await self.db.execute(
            delete(HealthMeasurement).where(HealthMeasurement.user_id == user_id, HealthMeasurement.source == source)
        )
        return result.rowcount or 0
