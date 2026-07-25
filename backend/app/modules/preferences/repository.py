import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.preferences.models import UserPreference


class PreferenceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(self, user_id: str) -> list[UserPreference]:
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id).order_by(UserPreference.key.asc())
        )
        return list(result.scalars().all())

    async def get(self, user_id: str, key: str) -> UserPreference | None:
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id, UserPreference.key == key)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: str, key: str, value: object) -> UserPreference:
        row = await self.get(user_id, key)
        payload = json.dumps(value)
        if row is None:
            row = UserPreference(user_id=user_id, key=key, value_json=payload)
            self.db.add(row)
        else:
            row.value_json = payload
            row.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    @staticmethod
    def parse_value(row: UserPreference | None) -> object:
        if row is None:
            return None
        try:
            return json.loads(row.value_json)
        except (json.JSONDecodeError, TypeError):
            return None
