
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import get_or_404
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
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[NotificationResponse], int]:
        items, total = await self.repo.list_notifications(
            user_id, unread_only=unread_only, limit=limit, offset=offset
        )
        return [NotificationResponse.model_validate(n) for n in items], total

    async def create(self, user_id: str, data: NotificationCreate) -> NotificationResponse:
        n = await self.repo.create(user_id, data)
        return NotificationResponse.model_validate(n)

    async def mark_read(self, user_id: str, notification_id: str) -> NotificationResponse:
        n = get_or_404(await self.repo.get_by_id(user_id, notification_id), "Notification not found")
        updated = await self.repo.mark_read(n)
        return NotificationResponse.model_validate(updated)

    async def mark_all_read(self, user_id: str) -> None:
        await self.repo.mark_all_read(user_id)

    async def delete(self, user_id: str, notification_id: str) -> None:
        n = get_or_404(await self.repo.get_by_id(user_id, notification_id), "Notification not found")
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
        n = get_or_404(await self.repo.get_by_id(user_id, notification_id), "Notification not found")

        from app.modules.integrations.notifications.notifier import NotifierMessage
        from app.modules.integrations.notifications.notifier_registry import build_user_notifier

        notifier = await build_user_notifier(self.repo.db, user_id, provider="telegram")
        if notifier is None:
            return TelegramSendResponse(sent=False, detail="Telegram not configured")

        result = await notifier.send(NotifierMessage(text=n.message, parse_mode="HTML"))
        if not result.ok:
            return TelegramSendResponse(sent=False, detail=result.detail or "Telegram send failed")

        n.telegram_sent = True
        await self.repo.db.flush()
        return TelegramSendResponse(sent=True, detail="Telegram message sent")

    async def get_dashboard_notifications(self, user_id: str, limit: int = 5) -> list[NotificationResponse]:
        items, _ = await self.list_notifications(user_id, unread_only=True, limit=limit)
        return items
