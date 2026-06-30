from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.models import IntegrationConnection
from app.modules.integrations.schemas import IntegrationCreate, IntegrationUpdate


class IntegrationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_connections(self, user_id: str) -> list[IntegrationConnection]:
        result = await self.db.execute(
            select(IntegrationConnection)
            .where(IntegrationConnection.user_id == user_id)
            .order_by(IntegrationConnection.provider)
        )
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, conn_id: str) -> IntegrationConnection | None:
        result = await self.db.execute(
            select(IntegrationConnection).where(
                IntegrationConnection.id == conn_id, IntegrationConnection.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_provider(self, user_id: str, provider: str) -> IntegrationConnection | None:
        result = await self.db.execute(
            select(IntegrationConnection).where(
                IntegrationConnection.user_id == user_id, IntegrationConnection.provider == provider
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: IntegrationCreate, display_name: str) -> IntegrationConnection:
        conn = IntegrationConnection(
            user_id=user_id,
            provider=data.provider,
            display_name=display_name,
            enabled=data.enabled,
            config_json=data.config_json,
            status="connected" if data.enabled else "disconnected",
        )
        self.db.add(conn)
        await self.db.flush()
        await self.db.refresh(conn)
        return conn

    async def update(self, conn: IntegrationConnection, data: IntegrationUpdate) -> IntegrationConnection:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(conn, key, value)
        if data.enabled is not None:
            conn.status = "connected" if data.enabled else "disconnected"
        await self.db.flush()
        await self.db.refresh(conn)
        return conn

    async def delete(self, conn: IntegrationConnection) -> None:
        await self.db.delete(conn)
