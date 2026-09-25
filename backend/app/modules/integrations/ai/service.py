"""BYOK config, connection test, and model catalog management for AI providers.

A provider's model list combines ids fetched from its model-list API (replaced on refresh)
with ids the user added manually (kept across refreshes).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.modules.ai.adapters.base import (
    CAPABILITY_CHAT,
    METADATA_TIMEOUT_SECONDS,
    AiProviderError,
    MalformedResponseError,
    ProviderAdapter,
    ProviderCredentials,
)
from app.modules.ai.adapters.registry import (
    BASE_URL_PROVIDERS,
    fallback_model,
    get_adapter,
    is_ai_provider,
    model_list_validates_key,
    provider_label,
    suggested_models,
    supports_model_listing,
)
from app.modules.ai.gateway import to_app_error
from app.modules.ai.models import AIProviderModel
from app.modules.ai.repository import AiRepository
from app.modules.integrations.ai.config import load_config, mask_config, parse_config, serialize_config
from app.modules.integrations.models import IntegrationConnection
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    AiModelAdd,
    AiModelItem,
    AiModelsResponse,
    AiModelTestResponse,
    AiProviderConfigStatus,
    AiProviderConfigUpdate,
    AiProviderTestResponse,
    IntegrationCreate,
    IntegrationUpdate,
)

MODEL_TEST_MAX_TOKENS = 16


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
            source=r.source,
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
            supports_model_listing=supports_model_listing(provider),
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
            refresh_error = await self._load_models_for_new_key(
                user_id, provider, _adapter(provider, new_key, base_url)
            )

        if "default_model" in fields and default_model and not data.custom_model:
            await self._require_listed_chat_model(user_id, provider, default_model)

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
            updated.status = "error" if refresh_error else "connected"
            if refresh_error is None and supports_model_listing(provider) and model_list_validates_key(provider):
                # An authenticated model listing is a live key check, so it counts as a successful test.
                updated.last_sync_at = datetime.now(timezone.utc)
            await self.repo.db.flush()
        return await self.status(user_id, provider, models_refresh_error=refresh_error)

    async def test(self, user_id: str, provider: str) -> AiProviderTestResponse:
        conn = await self._get_or_create(user_id, provider)
        cfg = parse_config(conn.config_json)
        if cfg is None:
            return AiProviderTestResponse(ok=False, detail=f"{provider_label(provider)} API key not configured")
        model = cfg.default_model or fallback_model(provider) or await self._first_chat_model(user_id, provider)
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
        if not supports_model_listing(provider):
            raise BadRequestError(
                f"{provider_label(provider)} has no model-list API. Add model ids manually."
            )
        cfg = parse_config(conn.config_json)
        if cfg is None:
            raise BadRequestError(
                {"code": "missing_credential", "message": f"Save a {provider_label(provider)} API key first."}
            )
        try:
            models = await _adapter(provider, cfg.api_key, cfg.base_url).list_models()
        except AiProviderError as exc:
            raise to_app_error(exc) from exc
        await self.ai_repo.replace_fetched_models(user_id, provider, models)
        return await self.list_models(user_id, provider)

    async def add_model(self, user_id: str, provider: str, data: AiModelAdd) -> AiModelsResponse:
        _require_ai_provider(provider)
        if not await self.ai_repo.add_manual_model(user_id, provider, data.model_id, data.capability):
            raise ConflictError(f"'{data.model_id}' is already in the {provider_label(provider)} model list.")
        return await self.list_models(user_id, provider)

    async def remove_model(self, user_id: str, provider: str, model_id: str) -> AiModelsResponse:
        _require_ai_provider(provider)
        if await self.ai_repo.remove_manual_model(user_id, provider, model_id):
            return await self.list_models(user_id, provider)
        rows = await self.ai_repo.list_models(user_id, provider)
        if any(r.model_id == model_id for r in rows):
            raise BadRequestError("Fetched models come from the provider's list and can't be removed.")
        raise NotFoundError(f"'{model_id}' is not in the {provider_label(provider)} model list.")

    async def test_model(self, user_id: str, provider: str, model_id: str) -> AiModelTestResponse:
        """A tiny chat call to one model: proves this key can use this exact model id."""
        conn = await self._get_or_create(user_id, provider)
        cfg = parse_config(conn.config_json)
        if cfg is None:
            return AiModelTestResponse(
                ok=False, detail=f"{provider_label(provider)} API key not configured", model_id=model_id
            )
        try:
            await _adapter(provider, cfg.api_key, cfg.base_url).chat(
                "Reply with the single word: ok",
                "ok",
                model=model_id,
                temperature=0.2,
                max_tokens=MODEL_TEST_MAX_TOKENS,
                timeout=METADATA_TIMEOUT_SECONDS,
            )
        except MalformedResponseError:
            # The call succeeded but returned no usable text (e.g. a reasoning model spent the
            # tiny token budget thinking) — the model is reachable with this key.
            return AiModelTestResponse(ok=True, detail="Reachable (empty reply)", model_id=model_id)
        except AiProviderError as exc:
            return AiModelTestResponse(ok=False, detail=str(exc), model_id=model_id)
        return AiModelTestResponse(ok=True, detail="Model responded", model_id=model_id)

    async def _load_models_for_new_key(
        self, user_id: str, provider: str, adapter: ProviderAdapter
    ) -> str | None:
        """Fetch the catalog (a live key check), or seed suggestions for vendors without one.

        Returns an error message instead of raising, so the key is still saved.
        """
        if not supports_model_listing(provider):
            if not await self.ai_repo.list_models(user_id, provider):
                for model_id in suggested_models(provider):
                    await self.ai_repo.add_manual_model(user_id, provider, model_id, CAPABILITY_CHAT)
            return None
        try:
            models = await adapter.list_models()
        except AiProviderError as exc:
            return str(exc)
        await self.ai_repo.replace_fetched_models(user_id, provider, models)
        return None

    async def _first_chat_model(self, user_id: str, provider: str) -> str | None:
        rows = await self.ai_repo.list_models(user_id, provider)
        return next((r.model_id for r in rows if CAPABILITY_CHAT in r.capability_set), None)

    async def _require_listed_chat_model(self, user_id: str, provider: str, model_id: str) -> None:
        rows = await self.ai_repo.list_models(user_id, provider)
        if not any(r.model_id == model_id and CAPABILITY_CHAT in r.capability_set for r in rows):
            raise BadRequestError(
                f"Model '{model_id}' is not in the {provider_label(provider)} model list. "
                "Fetch models or add the model id first."
            )
