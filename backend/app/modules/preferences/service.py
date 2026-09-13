
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.preferences.repository import PreferenceRepository
from app.modules.preferences.schemas import PreferenceListItem, PreferenceResponse
from app.core.exceptions import BadRequestError

class PreferenceService:
    def __init__(self, db: AsyncSession):
        self.repo = PreferenceRepository(db)

    async def list_preferences(self, user_id: str) -> list[PreferenceListItem]:
        rows = await self.repo.list_for_user(user_id)
        return [
            PreferenceListItem(
                key=r.key,
                value=PreferenceRepository.parse_value(r),
                updated_at=r.updated_at,
            )
            for r in rows
        ]

    async def get_preference(self, user_id: str, key: str) -> PreferenceResponse:
        if not key or len(key) > 64:
            raise BadRequestError("Invalid preference key")
        row = await self.repo.get(user_id, key)
        return PreferenceResponse(
            key=key,
            value=PreferenceRepository.parse_value(row),
            updated_at=row.updated_at if row else None,
        )

    async def put_preference(self, user_id: str, key: str, value: object) -> PreferenceResponse:
        if not key or len(key) > 64:
            raise BadRequestError("Invalid preference key")
        row = await self.repo.upsert(user_id, key, value)
        return PreferenceResponse(
            key=row.key,
            value=PreferenceRepository.parse_value(row),
            updated_at=row.updated_at,
        )
