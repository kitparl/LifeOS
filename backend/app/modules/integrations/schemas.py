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
