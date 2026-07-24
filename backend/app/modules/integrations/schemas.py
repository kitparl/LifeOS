from datetime import datetime

from pydantic import BaseModel, Field


class IntegrationProviderInfo(BaseModel):
    provider: str
    display_name: str
    description: str
    oauth_required: bool


class IntegrationCreate(BaseModel):
    provider: str
    display_name: str | None = None
    enabled: bool = False
    config_json: str | None = None


class IntegrationUpdate(BaseModel):
    display_name: str | None = None
    enabled: bool | None = None
    config_json: str | None = None


class IntegrationResponse(BaseModel):
    id: str
    provider: str
    display_name: str
    enabled: bool
    config_json: str | None
    status: str
    last_sync_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IntegrationSyncResponse(BaseModel):
    provider: str
    status: str
    message: str
    synced_at: datetime


class TelegramConfigUpdate(BaseModel):
    bot_token: str | None = Field(default=None, max_length=200)
    chat_id: str | None = Field(default=None, max_length=64)
    enabled: bool | None = None


class TelegramConfigStatus(BaseModel):
    connection_id: str
    provider: str = "telegram"
    enabled: bool
    status: str
    configured: bool
    bot_token_masked: str | None = None
    chat_id: str | None = None
    last_sync_at: datetime | None = None
    last_digest_at: datetime | None = None


class TelegramTestResponse(BaseModel):
    ok: bool
    detail: str
    bot_username: str | None = None


class DetectChatIdRequest(BaseModel):
    """Optional token override so chat id can be detected before saving."""

    bot_token: str | None = Field(default=None, max_length=200)


class ChatCandidate(BaseModel):
    chat_id: str
    type: str | None = None
    title: str | None = None
    username: str | None = None


class DetectChatIdResponse(BaseModel):
    candidates: list[ChatCandidate]
    detail: str


class DigestResponse(BaseModel):
    sent: bool
    detail: str
    sections: dict[str, int] = Field(default_factory=dict)
