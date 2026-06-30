from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    TelegramSendResponse,
)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.repo = NotificationRepository(db)

    async def list_notifications(
        self, user_id: str, unread_only: bool = False, limit: int = 50
    ) -> list[NotificationResponse]:
        items = await self.repo.list_notifications(user_id, unread_only=unread_only, limit=limit)
        return [NotificationResponse.model_validate(n) for n in items]

    async def create(self, user_id: str, data: NotificationCreate) -> NotificationResponse:
        n = await self.repo.create(user_id, data)
        return NotificationResponse.model_validate(n)

    async def mark_read(self, user_id: str, notification_id: str) -> NotificationResponse:
        n = await self.repo.get_by_id(user_id, notification_id)
        if n is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        updated = await self.repo.mark_read(n)
        return NotificationResponse.model_validate(updated)

    async def mark_all_read(self, user_id: str) -> None:
        await self.repo.mark_all_read(user_id)

    async def delete(self, user_id: str, notification_id: str) -> None:
        n = await self.repo.get_by_id(user_id, notification_id)
        if n is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        await self.repo.delete(n)

    async def get_settings(self, user_id: str) -> NotificationSettingsResponse:
        settings = await self.repo.get_settings(user_id)
        return NotificationSettingsResponse.model_validate(settings)

    async def update_settings(
        self, user_id: str, data: NotificationSettingsUpdate
    ) -> NotificationSettingsResponse:
        settings = await self.repo.update_settings(user_id, data)
        return NotificationSettingsResponse.model_validate(settings)

    async def send_telegram(self, user_id: str, notification_id: str) -> TelegramSendResponse:
        n = await self.repo.get_by_id(user_id, notification_id)
        if n is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        settings = await self.repo.get_settings(user_id)
        if not settings.telegram_enabled or not settings.telegram_chat_id:
            return TelegramSendResponse(sent=False, detail="Telegram not configured")
        n.telegram_sent = True
        await self.repo.db.flush()
        return TelegramSendResponse(sent=True, detail="Telegram delivery queued (stub)")

    async def get_dashboard_notifications(self, user_id: str, limit: int = 5) -> list[NotificationResponse]:
        return await self.list_notifications(user_id, unread_only=True, limit=limit)
