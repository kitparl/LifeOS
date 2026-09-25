"""BYOK config, connection test, and model catalog refresh for AI providers."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.ai.adapters.base import (
    CAPABILITY_CHAT,
    AiProviderError,
    ProviderAdapter,
    ProviderCredentials,
)
from app.modules.ai.adapters.registry import (
    BASE_URL_PROVIDERS,
    fallback_model,
    get_adapter,
    is_ai_provider,
    provider_label,
)
from app.modules.ai.gateway import to_app_error
from app.modules.ai.models import AIProviderModel
from app.modules.ai.repository import AiRepository
from app.modules.integrations.ai.config import load_config, mask_config, parse_config, serialize_config
from app.modules.integrations.models import IntegrationConnection
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    AiModelItem,
    AiModelsResponse,
    AiProviderConfigStatus,
    AiProviderConfigUpdate,
    AiProviderTestResponse,
    IntegrationCreate,
    IntegrationUpdate,
)


def _require_ai_provider(provider: str) -> None:
    if not is_ai_provider(provider):
        raise NotFoundError(f"Unknown AI provider: {provider}")


def _adapter(provider: str, api_key: str, base_url: str | None) -> ProviderAdapter:
    allowed_base_url = base_url if provider in BASE_URL_PROVIDERS else None
    return get_adapter(provider, ProviderCredentials(api_key=api_key, base_url=allowed_base_url))


def _to_model_items(rows: list[AIProviderModel]) -> list[AiModelItem]:
    return [
        AiModelItem(
            model_id=r.model_id,
            display_name=r.display_name,
            capabilities=sorted(r.capability_set),
        )
        for r in rows
    ]


class AiProviderIntegrationService:
    def __init__(self, db: AsyncSession):
        self.repo = IntegrationRepository(db)
        self.ai_repo = AiRepository(db)

    async def _get_or_create(self, user_id: str, provider: str) -> IntegrationConnection:
        _require_ai_provider(provider)
        conn = await self.repo.get_by_provider(user_id, provider)
        if conn is not None:
            return conn
        from app.modules.integrations.service import PROVIDER_CATALOG

        catalog = next((p for p in PROVIDER_CATALOG if p.provider == provider), None)
        display_name = catalog.display_name if catalog else provider_label(provider)
        return await self.repo.create(user_id, IntegrationCreate(provider=provider, enabled=False), display_name)

    async def status(
        self, user_id: str, provider: str, *, models_refresh_error: str | None = None
    ) -> AiProviderConfigStatus:
        conn = await self._get_or_create(user_id, provider)
        masked = mask_config(conn.config_json)
        models = await self.ai_repo.list_models(user_id, provider)
        return AiProviderConfigStatus(
            connection_id=conn.id,
            provider=provider,
            display_name=conn.display_name,
            enabled=conn.enabled,
            status=conn.status,
            configured=masked.configured,
            api_key_masked=masked.api_key_masked,
            default_model=masked.default_model,
            base_url=masked.base_url,
            supports_base_url=provider in BASE_URL_PROVIDERS,
            last_tested_at=conn.last_sync_at,
            last_test_ok={"connected": True, "error": False}.get(conn.status),
            models_refreshed_at=max((m.refreshed_at for m in models), default=None),
            model_count=len(models),
            models_refresh_error=models_refresh_error,
        )

    async def save(self, user_id: str, provider: str, data: AiProviderConfigUpdate) -> AiProviderConfigStatus:
        conn = await self._get_or_create(user_id, provider)
        fields = data.model_fields_set - {"custom_model"}
        if not fields:
            raise BadRequestError("No fields to update")
        if data.base_url and provider not in BASE_URL_PROVIDERS:
            raise BadRequestError("A custom base URL is only supported for OpenAI.")

        existing = load_config(conn.config_json)
        new_key = (data.api_key or "").strip()
        base_url = data.base_url if "base_url" in fields else existing.base_url
        default_model = data.default_model if "default_model" in fields else existing.default_model

        refresh_error: str | None = None
        if new_key:
            try:
                await self._refresh(user_id, provider, _adapter(provider, new_key, base_url))
            except AiProviderError as exc:
                refresh_error = str(exc)

        if "default_model" in fields and default_model and not data.custom_model:
            await self._require_cached_chat_model(user_id, provider, default_model)

        update = IntegrationUpdate(
            config_json=serialize_config(
                existing_json=conn.config_json,
                api_key=new_key or None,
                default_model=default_model,
                base_url=base_url,
            )
        )
        if data.enabled is not None:
            update.enabled = data.enabled
        elif new_key:
            update.enabled = True
        updated = await self.repo.update(conn, update)

        if new_key:
            # Listing models is a live key check, so a new key's status reflects it.
            updated.status = "error" if refresh_error else "connected"
            if refresh_error is None:
                updated.last_sync_at = datetime.now(timezone.utc)
            await self.repo.db.flush()
        return await self.status(user_id, provider, models_refresh_error=refresh_error)

    async def test(self, user_id: str, provider: str) -> AiProviderTestResponse:
        conn = await self._get_or_create(user_id, provider)
        cfg = parse_config(conn.config_json)
        if cfg is None:
            return AiProviderTestResponse(ok=False, detail=f"{provider_label(provider)} API key not configured")
        model = cfg.default_model or fallback_model(provider)
        try:
            await _adapter(provider, cfg.api_key, cfg.base_url).test(model)
        except AiProviderError as exc:
            conn.status = "error"
            await self.repo.db.flush()
            return AiProviderTestResponse(ok=False, detail=str(exc), model=model)
        conn.status = "connected"
        conn.last_sync_at = datetime.now(timezone.utc)
        await self.repo.db.flush()
        return AiProviderTestResponse(ok=True, detail=f"{provider_label(provider)} API key verified", model=model)

    async def list_models(self, user_id: str, provider: str) -> AiModelsResponse:
        _require_ai_provider(provider)
        rows = await self.ai_repo.list_models(user_id, provider)
        return AiModelsResponse(
            provider=provider,
            models=_to_model_items(rows),
            refreshed_at=max((r.refreshed_at for r in rows), default=None),
        )

    async def refresh_models(self, user_id: str, provider: str) -> AiModelsResponse:
        conn = await self._get_or_create(user_id, provider)
        cfg = parse_config(conn.config_json)
        if cfg is None:
            raise BadRequestError(
                {"code": "missing_credential", "message": f"Save a {provider_label(provider)} API key first."}
            )
        try:
            await self._refresh(user_id, provider, _adapter(provider, cfg.api_key, cfg.base_url))
        except AiProviderError as exc:
            raise to_app_error(exc) from exc
        return await self.list_models(user_id, provider)

    async def _refresh(self, user_id: str, provider: str, adapter: ProviderAdapter) -> None:
        models = await adapter.list_models()
        await self.ai_repo.replace_models(user_id, provider, models)

    async def _require_cached_chat_model(self, user_id: str, provider: str, model_id: str) -> None:
        rows = await self.ai_repo.list_models(user_id, provider)
        if not any(r.model_id == model_id and CAPABILITY_CHAT in r.capability_set for r in rows):
            raise BadRequestError(
                f"Model '{model_id}' is not in the {provider_label(provider)} model list. "
                "Refresh models, or enable 'Use custom model id'."
            )
