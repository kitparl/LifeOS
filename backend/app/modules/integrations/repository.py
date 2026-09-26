from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.modules.integrations.models import IntegrationConnection
from app.modules.integrations.schemas import IntegrationCreate, IntegrationUpdate


class IntegrationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_connections(
        self, user_id: str, limit: int = 25, offset: int = 0
    ) -> tuple[list[IntegrationConnection], int]:
        q = (
            select(IntegrationConnection)
            .where(IntegrationConnection.user_id == user_id)
            .order_by(IntegrationConnection.provider)
        )
        return await paginate(self.db, q, Pagination(limit=limit, offset=offset))

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

    async def get_by_webhook_secret(self, secret: str) -> IntegrationConnection | None:
        if not secret:
            return None
        result = await self.db.execute(
            select(IntegrationConnection).where(
                IntegrationConnection.webhook_secret == secret,
                IntegrationConnection.provider == "telegram",
            )
        )
        return result.scalar_one_or_none()

    async def list_enabled_telegram(self) -> list[IntegrationConnection]:
        result = await self.db.execute(
            select(IntegrationConnection).where(
                IntegrationConnection.provider == "telegram",
                IntegrationConnection.enabled.is_(True),
            )
        )
        return list(result.scalars().all())

    async def list_enabled_by_provider(self, provider: str) -> list[IntegrationConnection]:
        result = await self.db.execute(
            select(IntegrationConnection).where(
                IntegrationConnection.provider == provider,
                IntegrationConnection.enabled.is_(True),
            )
        )
        return list(result.scalars().all())

    async def get_or_create(self, user_id: str, provider: str, display_name: str) -> IntegrationConnection:
        """The user's connection for ``provider``, created disabled on first use."""
        conn = await self.get_by_provider(user_id, provider)
        if conn is not None:
            return conn
        return await self.create(user_id, IntegrationCreate(provider=provider, enabled=False), display_name)

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
