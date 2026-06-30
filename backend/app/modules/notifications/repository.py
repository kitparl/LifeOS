from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import Notification, NotificationSettings
from app.modules.notifications.schemas import NotificationCreate, NotificationSettingsUpdate


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_notifications(
        self, user_id: str, unread_only: bool = False, limit: int = 50
    ) -> list[Notification]:
        q = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            q = q.where(Notification.is_read.is_(False))
        q = q.order_by(Notification.created_at.desc()).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, notification_id: str) -> Notification | None:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, data: NotificationCreate) -> Notification:
        n = Notification(
            user_id=user_id,
            message=data.message,
            module=data.module,
            entity_id=data.entity_id,
            route=data.route,
        )
        self.db.add(n)
        await self.db.flush()
        await self.db.refresh(n)
        return n

    async def mark_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    async def mark_all_read(self, user_id: str) -> None:
        await self.db.execute(
            update(Notification).where(Notification.user_id == user_id).values(is_read=True)
        )
        await self.db.flush()

    async def delete(self, notification: Notification) -> None:
        await self.db.delete(notification)
        await self.db.flush()

    async def get_settings(self, user_id: str) -> NotificationSettings:
        result = await self.db.execute(
            select(NotificationSettings).where(NotificationSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = NotificationSettings(user_id=user_id)
            self.db.add(settings)
            await self.db.flush()
            await self.db.refresh(settings)
        return settings

    async def update_settings(self, user_id: str, data: NotificationSettingsUpdate) -> NotificationSettings:
        settings = await self.get_settings(user_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(settings, key, value)
        await self.db.flush()
        await self.db.refresh(settings)
        return settings
