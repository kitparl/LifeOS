from functools import lru_cache
from typing import Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_ENVS = frozenset({"dev", "development", "local"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    app_name: str = "LifeOS API"
    app_env: str = Field(default="production", validation_alias="ENV")
    database_url: str = "sqlite+aiosqlite:///./lifeos_dev.db"
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:4200"
    cookie_secure: bool | None = Field(default=None, validation_alias="COOKIE_SECURE")
    google_client_id: str = ""
    github_client_id: str = ""
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 10 * 1024 * 1024
    openai_api_key: str = ""
    ai_chat_model: str = "gpt-4o-mini"
    ai_embedding_model: str = "text-embedding-3-small"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not value:
            return value
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://") and "+asyncpg" not in value:
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @model_validator(mode="after")
    def apply_env_defaults(self) -> Self:
        if self.cookie_secure is None:
            self.cookie_secure = self.is_production
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in _DEV_ENVS

    @property
    def is_production(self) -> bool:
        return not self.is_development

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
