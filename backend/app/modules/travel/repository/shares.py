from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.travel.models import (
    TravelShareContributor,
    TravelShareEvent,
    TravelShareVersion,
    TravelTripShare,
)


class ShareRepository:
    """Every query is scoped by its parent: the owner's user id for shares, the share id below that."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- shares -----------------------------------------------------------------------------

    async def get_for_trip(self, user_id: str, trip_id: str) -> TravelTripShare | None:
        result = await self.db.execute(
            select(TravelTripShare).where(TravelTripShare.trip_id == trip_id, TravelTripShare.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> TravelTripShare | None:
        result = await self.db.execute(select(TravelTripShare).where(TravelTripShare.code == code))
        return result.scalar_one_or_none()

    async def code_exists(self, code: str) -> bool:
        result = await self.db.execute(select(TravelTripShare.id).where(TravelTripShare.code == code))
        return result.first() is not None

    async def add(self, row: object) -> None:
        self.db.add(row)
        await self.db.flush()

    async def flush(self) -> None:
        await self.db.flush()

    # ---- contributors -----------------------------------------------------------------------

    async def contributors(self, share_id: str) -> list[TravelShareContributor]:
        result = await self.db.execute(
            select(TravelShareContributor)
            .where(TravelShareContributor.share_id == share_id)
            .order_by(TravelShareContributor.created_at)
        )
        return list(result.scalars().all())

    async def get_contributor(self, share_id: str, contributor_id: str) -> TravelShareContributor | None:
        result = await self.db.execute(
            select(TravelShareContributor).where(
                TravelShareContributor.share_id == share_id, TravelShareContributor.id == contributor_id
            )
        )
        return result.scalar_one_or_none()

    async def contributor_by_sub(self, share_id: str, google_sub: str) -> TravelShareContributor | None:
        result = await self.db.execute(
            select(TravelShareContributor).where(
                TravelShareContributor.share_id == share_id, TravelShareContributor.google_sub == google_sub
            )
        )
        return result.scalar_one_or_none()

    async def contributor_by_secret(self, share_id: str, secret_hash: str) -> TravelShareContributor | None:
        result = await self.db.execute(
            select(TravelShareContributor).where(
                TravelShareContributor.share_id == share_id, TravelShareContributor.secret_hash == secret_hash
            )
        )
        return result.scalar_one_or_none()

    async def count_contributors(self, share_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(TravelShareContributor).where(TravelShareContributor.share_id == share_id)
        )
        return result.scalar_one()

    # ---- versions ---------------------------------------------------------------------------

    async def versions(self, share_id: str) -> list[TravelShareVersion]:
        """Latest edited first (index `ix_travel_share_versions_share_updated`)."""
        result = await self.db.execute(
            select(TravelShareVersion)
            .where(TravelShareVersion.share_id == share_id)
            .order_by(TravelShareVersion.updated_at.desc(), TravelShareVersion.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_version(self, share_id: str, version_id: str) -> TravelShareVersion | None:
        result = await self.db.execute(
            select(TravelShareVersion).where(
                TravelShareVersion.share_id == share_id, TravelShareVersion.id == version_id
            )
        )
        return result.scalar_one_or_none()

    async def plan_for(self, share_id: str, contributor_id: str) -> TravelShareVersion | None:
        result = await self.db.execute(
            select(TravelShareVersion).where(
                TravelShareVersion.share_id == share_id,
                TravelShareVersion.contributor_id == contributor_id,
                TravelShareVersion.kind == "plan",
            )
        )
        return result.scalar_one_or_none()

    async def versions_of_kind(self, share_id: str, kind: str) -> list[TravelShareVersion]:
        result = await self.db.execute(
            select(TravelShareVersion).where(TravelShareVersion.share_id == share_id, TravelShareVersion.kind == kind)
        )
        return list(result.scalars().all())

    async def delete_version(self, version: TravelShareVersion) -> None:
        await self.db.delete(version)
        await self.db.flush()

    # ---- events -----------------------------------------------------------------------------

    async def events(self, share_id: str, limit: int) -> list[TravelShareEvent]:
        result = await self.db.execute(
            select(TravelShareEvent)
            .where(TravelShareEvent.share_id == share_id)
            .order_by(TravelShareEvent.at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
