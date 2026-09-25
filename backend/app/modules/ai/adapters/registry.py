"""Provider name -> adapter factory. Adding a vendor = one adapter module + one entry here."""

from __future__ import annotations

from collections.abc import Callable

from app.modules.ai.adapters import sarvam
from app.modules.ai.adapters.anthropic import AnthropicAdapter
from app.modules.ai.adapters.base import ProviderAdapter, ProviderCredentials
from app.modules.ai.adapters.gemini import GeminiAdapter
from app.modules.ai.adapters.openai import OpenAiAdapter

_ADAPTERS: dict[str, Callable[[ProviderCredentials], ProviderAdapter]] = {
    "openai": OpenAiAdapter,
    "anthropic": AnthropicAdapter,
    "gemini": GeminiAdapter,
    "sarvam": sarvam.SarvamAdapter,
}

# Also the resolution order when a use case has no explicit selection.
AI_PROVIDERS: tuple[str, ...] = tuple(_ADAPTERS)

# Providers that accept a custom base URL (OpenAI-compatible endpoints).
BASE_URL_PROVIDERS: frozenset[str] = frozenset({"openai"})

# Model used when a connected provider has no default model saved yet.
_FALLBACK_MODELS: dict[str, str] = {"sarvam": sarvam.DEFAULT_MODEL}


def is_ai_provider(provider: str) -> bool:
    return provider in _ADAPTERS


def get_adapter(provider: str, credentials: ProviderCredentials) -> ProviderAdapter:
    try:
        factory = _ADAPTERS[provider]
    except KeyError as exc:
        raise ValueError(f"Unknown AI provider: {provider}") from exc
    return factory(credentials)


def provider_label(provider: str) -> str:
    factory = _ADAPTERS.get(provider)
    return str(getattr(factory, "label", provider))


def fallback_model(provider: str) -> str | None:
    return _FALLBACK_MODELS.get(provider)
