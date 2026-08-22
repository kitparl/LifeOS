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
    notify_on: list[str] | None = None
    digest_enabled: bool | None = None
    digest_time: str | None = Field(default=None, max_length=5)
    digest_frequency: str | None = Field(default=None, max_length=16)
    digest_weekday: int | None = Field(default=None, ge=0, le=6)
    timezone: str | None = Field(default=None, max_length=64)
    morning_enabled: bool | None = None
    morning_time: str | None = Field(default=None, max_length=5)
    midday_enabled: bool | None = None
    midday_time: str | None = Field(default=None, max_length=5)
    night_enabled: bool | None = None
    night_time: str | None = Field(default=None, max_length=5)
    weekly_enabled: bool | None = None
    weekly_time: str | None = Field(default=None, max_length=5)
    weekly_weekday: int | None = Field(default=None, ge=0, le=6)
    ai_briefing_enabled: bool | None = None
    ai_briefing_time: str | None = Field(default=None, max_length=5)
    birthday_reminders_enabled: bool | None = None
    immutable_reminders_enabled: bool | None = None
    routine_reminders_enabled: bool | None = None


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
    notify_on: list[str] = Field(default_factory=list)
    digest_enabled: bool = False
    digest_time: str = "06:00"
    digest_frequency: str = "daily"
    digest_weekday: int = 0
    timezone: str = "Asia/Kolkata"
    morning_enabled: bool = True
    morning_time: str = "06:00"
    midday_enabled: bool = True
    midday_time: str = "12:30"
    night_enabled: bool = True
    night_time: str = "22:00"
    weekly_enabled: bool = True
    weekly_time: str = "18:00"
    weekly_weekday: int = 6
    ai_briefing_enabled: bool = False
    ai_briefing_time: str = "08:00"
    birthday_reminders_enabled: bool = True
    immutable_reminders_enabled: bool = True
    routine_reminders_enabled: bool = True
    webhook_configured: bool = False
    webhook_url: str | None = None
    # Next fire time per cron job type as currently registered in the scheduler.
    next_runs: dict[str, datetime | None] = Field(default_factory=dict)
    # Set when preferences were stored but the scheduler could not be updated.
    scheduler_warning: str | None = None


class ReportRunResponse(BaseModel):
    id: str
    job_type: str
    job_id: str
    status: str
    skip_reason: str | None = None
    error: str | None = None
    sections_json: str | None = None
    dedupe_key: str | None = None
    message_chars: int | None = None
    scheduled_for: datetime | None = None
    started_at: datetime
    finished_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TelegramWebhookStatus(BaseModel):
    configured: bool
    url: str | None = None
    pending_update_count: int | None = None
    last_error_message: str | None = None
    detail: str = ""


class TelegramWebhookRegisterResponse(BaseModel):
    ok: bool
    detail: str
    webhook_url: str | None = None



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


class GitHubConfigUpdate(BaseModel):
    token: str | None = Field(default=None, max_length=200)
    repo: str | None = Field(default=None, max_length=400)
    branch: str | None = Field(default=None, max_length=64)
    base_path: str | None = Field(default=None, max_length=200)
    enabled: bool | None = None
    notify_github_sync_in_app: bool | None = None
    notify_github_sync_telegram: bool | None = None


class GitHubConfigStatus(BaseModel):
    connection_id: str
    provider: str = "github"
    enabled: bool
    status: str
    configured: bool
    token_masked: str | None = None
    repo: str | None = None
    branch: str = "main"
    base_path: str = ""
    notify_github_sync_in_app: bool = False
    notify_github_sync_telegram: bool = False
    last_sync_at: datetime | None = None


class GitHubTestResponse(BaseModel):
    ok: bool
    detail: str
    repo_full_name: str | None = None
    branch: str | None = None
    can_push: bool | None = None


class GitHubSyncResponse(BaseModel):
    status: str
    message: str
    md_path: str | None = None
    synced_at: datetime | None = None
    remote_commit_sha: str | None = None
