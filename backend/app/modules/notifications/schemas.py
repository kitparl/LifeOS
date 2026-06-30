from datetime import datetime

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    message: str = Field(min_length=1)
    module: str | None = None
    entity_id: str | None = None
    route: str | None = None


class NotificationResponse(BaseModel):
    id: str
    message: str
    module: str | None
    entity_id: str | None
    route: str | None
    is_read: bool
    channel: str
    telegram_sent: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationSettingsResponse(BaseModel):
    telegram_chat_id: str | None
    telegram_enabled: bool

    model_config = {"from_attributes": True}


class NotificationSettingsUpdate(BaseModel):
    telegram_chat_id: str | None = None
    telegram_enabled: bool | None = None


class TelegramSendResponse(BaseModel):
    sent: bool
    detail: str
