from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.core.timezone import utc_now
from app.modules.integrations.garmin.models import ACTIVE_STATUSES, JOB_INTERRUPTED, GarminImportJob


class GarminImportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, range_mode: str) -> GarminImportJob:
        job = GarminImportJob(user_id=user_id, range_mode=range_mode)
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def get(self, user_id: str, job_id: str) -> GarminImportJob | None:
        result = await self.db.execute(
            select(GarminImportJob).where(GarminImportJob.id == job_id, GarminImportJob.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def has_active(self, user_id: str) -> bool:
        count = await self.db.scalar(
            select(func.count())
            .select_from(GarminImportJob)
            .where(GarminImportJob.user_id == user_id, GarminImportJob.status.in_(ACTIVE_STATUSES))
        )
        return bool(count)

    async def list_page(self, user_id: str, limit: int, offset: int) -> tuple[list[GarminImportJob], int]:
        query = (
            select(GarminImportJob)
            .where(GarminImportJob.user_id == user_id)
            .order_by(GarminImportJob.created_at.desc())
        )
        return await paginate(self.db, query, Pagination(limit=limit, offset=offset))

    async def update_fields(self, job_id: str, **values: object) -> None:
        """Write plain values with an UPDATE, so no ORM object has to survive a rollback."""
        await self.db.execute(update(GarminImportJob).where(GarminImportJob.id == job_id).values(**values))

    async def mark_interrupted(self, now: datetime | None = None) -> int:
        result = await self.db.execute(
            update(GarminImportJob)
            .where(GarminImportJob.status.in_(ACTIVE_STATUSES))
            .values(status=JOB_INTERRUPTED, finished_at=now or utc_now())
        )
        return result.rowcount or 0
