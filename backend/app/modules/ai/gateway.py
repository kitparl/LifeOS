"""AI gateway: use case -> (provider, model) -> credentials -> adapter.

Every domain call site goes through here, so no domain code branches on a vendor.
Credential precedence: Integrations BYOK (enabled + key) > env OPENAI_API_KEY (OpenAI only).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    AppError,
    BadGatewayError,
    BadRequestError,
    ServiceUnavailableError,
    UnauthorizedError,
)
from app.modules.ai.adapters.base import (
    AiProviderError,
    EmbeddingProvider,
    InvalidCredentialError,
    MalformedResponseError,
    MissingCredentialError,
    ProviderAdapter,
    ProviderCredentials,
    ProviderRequestError,
)
from app.modules.ai.adapters.openai import OpenAiAdapter
from app.modules.ai.adapters.registry import (
    AI_PROVIDERS,
    BASE_URL_PROVIDERS,
    fallback_model,
    get_adapter,
    provider_label,
)
from app.modules.ai.repository import AiRepository
from app.modules.ai.schemas import AiSettings
from app.modules.ai.use_cases import get_use_case
from app.modules.integrations.ai.config import AiProviderConfig, parse_config
from app.modules.integrations.repository import IntegrationRepository

ENV_PROVIDER = "openai"


@dataclass(frozen=True)
class ResolvedModel:
    provider: str
    model: str
    adapter: ProviderAdapter
    settings: AiSettings


def to_app_error(exc: AiProviderError) -> AppError:
    """Map a vendor error to the HTTP error returned to the client ({"code", "message"})."""
    detail = {"code": exc.code, "message": str(exc)}
    if isinstance(exc, ProviderRequestError):
        return BadRequestError(detail)
    if isinstance(exc, InvalidCredentialError):
        return UnauthorizedError(detail)
    if isinstance(exc, MissingCredentialError):
        return BadRequestError(detail)
    if isinstance(exc, MalformedResponseError):
        return BadGatewayError(detail)
    return ServiceUnavailableError(detail)


class AiGateway:
    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.app_settings = settings or get_settings()
        self.repo = AiRepository(db)
        self.integrations = IntegrationRepository(db)
        self._configs: dict[tuple[str, str], AiProviderConfig | None] = {}

    async def provider_config(self, user_id: str, provider: str) -> AiProviderConfig | None:
        """The user's enabled BYOK config for a provider, if it has a usable key."""
        cache_key = (user_id, provider)
        if cache_key not in self._configs:
            conn = await self.integrations.get_by_provider(user_id, provider)
            self._configs[cache_key] = (
                parse_config(conn.config_json) if conn is not None and conn.enabled else None
            )
        return self._configs[cache_key]

    async def credentials(self, user_id: str, provider: str) -> ProviderCredentials | None:
        cfg = await self.provider_config(user_id, provider)
        if cfg is not None:
            base_url = cfg.base_url if provider in BASE_URL_PROVIDERS else None
            return ProviderCredentials(api_key=cfg.api_key, base_url=base_url)
        env_key = self.app_settings.openai_api_key.strip()
        if provider == ENV_PROVIDER and env_key:
            return ProviderCredentials(api_key=env_key)
        return None

    async def ai_settings(self, user_id: str) -> AiSettings:
        return await self.repo.get_ai_settings(user_id)

    async def resolve(self, user_id: str, use_case: str) -> ResolvedModel:
        """Resolve the model for a use case. Raises MissingCredentialError when nothing is usable."""
        uc = get_use_case(use_case)
        if uc is None:
            raise ValueError(f"Unknown AI use case: {use_case}")
        settings = await self.ai_settings(user_id)

        selection = await self.repo.get_selection(user_id, use_case)
        if selection is not None:
            creds = await self.credentials(user_id, selection.provider)
            if creds is None:
                raise MissingCredentialError(
                    f"Connect your {provider_label(selection.provider)} API key in "
                    f"Integrations → AI to use {uc.display_name}."
                )
            return ResolvedModel(
                provider=selection.provider,
                model=selection.model,
                adapter=get_adapter(selection.provider, creds),
                settings=settings,
            )

        order = list(AI_PROVIDERS)
        if settings.default_provider in order:
            order.remove(settings.default_provider)
            order.insert(0, settings.default_provider)
        for provider in order:
            creds = await self.credentials(user_id, provider)
            if creds is None:
                continue
            model = await self._default_model(user_id, provider, uc.capability)
            if model:
                return ResolvedModel(
                    provider=provider,
                    model=model,
                    adapter=get_adapter(provider, creds),
                    settings=settings,
                )
        raise MissingCredentialError(
            f"No AI provider is connected. Connect one in Integrations → AI to use {uc.display_name}."
        )

    async def _default_model(self, user_id: str, provider: str, capability: str) -> str | None:
        cfg = await self.provider_config(user_id, provider)
        if cfg is not None and cfg.default_model:
            return cfg.default_model
        if provider == ENV_PROVIDER and self.app_settings.ai_chat_model:
            return self.app_settings.ai_chat_model
        seeded = fallback_model(provider)
        if seeded:
            return seeded
        cached = await self.repo.list_models(user_id, provider)
        return next((m.model_id for m in cached if capability in m.capability_set), None)

    async def chat(
        self,
        user_id: str,
        use_case: str,
        system: str,
        message: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        resolved = await self.resolve(user_id, use_case)
        s = resolved.settings
        result = await resolved.adapter.chat(
            system,
            message,
            model=resolved.model,
            temperature=s.temperature if temperature is None else temperature,
            max_tokens=s.max_tokens if max_tokens is None else max_tokens,
            timeout=float(s.timeout_seconds),
        )
        return result.text

    async def embedding_adapter(self, user_id: str) -> tuple[EmbeddingProvider, str] | None:
        """Embeddings stay on OpenAI (BYOK > env) so stored RAG vectors keep one model."""
        creds = await self.credentials(user_id, ENV_PROVIDER)
        if creds is None:
            return None
        return OpenAiAdapter(creds), self.app_settings.ai_embedding_model
