from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activities.models import Activity, ActivitySeries
from app.modules.auth.models import User


class ActivityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: str, activity_id: str) -> Activity | None:
        result = await self.db.execute(select(Activity).where(Activity.id == activity_id, Activity.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_by_external(self, user_id: str, source: str, external_id: str) -> Activity | None:
        result = await self.db.execute(
            select(Activity).where(
                Activity.user_id == user_id, Activity.source == source, Activity.external_id == external_id
            )
        )
        return result.scalar_one_or_none()

    async def user_timezone(self, user_id: str) -> str | None:
        return await self.db.scalar(select(User.timezone).where(User.id == user_id))

    async def add(self, activity: Activity, series: ActivitySeries | None) -> None:
        self.db.add(activity)
        await self.db.flush()
        if series is not None:
            series.activity_id = activity.id
            self.db.add(series)
            await self.db.flush()

    async def get_series(self, activity_id: str) -> ActivitySeries | None:
        return await self.db.get(ActivitySeries, activity_id)

    async def list_by_source(self, user_id: str, source: str) -> list[Activity]:
        result = await self.db.execute(select(Activity).where(Activity.user_id == user_id, Activity.source == source))
        return list(result.scalars().all())

    async def delete_many(self, activity_ids: list[str]) -> None:
        if not activity_ids:
            return
        await self.db.execute(delete(ActivitySeries).where(ActivitySeries.activity_id.in_(activity_ids)))
        await self.db.execute(delete(Activity).where(Activity.id.in_(activity_ids)))
        await self.db.flush()
