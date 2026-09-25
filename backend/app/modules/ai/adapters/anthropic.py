"""Anthropic adapter (Messages API, Models API)."""

from __future__ import annotations

from app.modules.ai.adapters.base import (
    CAPABILITY_CHAT,
    CAPABILITY_VISION,
    METADATA_TIMEOUT_SECONDS,
    MODEL_ID_MAX_LENGTH,
    ChatResult,
    MalformedResponseError,
    ModelInfo,
    ProviderCredentials,
    normalize_usage,
    request_json,
)

BASE_URL = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"
_MODELS_PAGE_LIMIT = 1000


class AnthropicAdapter:
    label = "Anthropic"
    supports_model_listing = True

    def __init__(self, credentials: ProviderCredentials):
        self._api_key = credentials.api_key

    @property
    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self._api_key, "anthropic-version": ANTHROPIC_VERSION}

    async def chat(
        self,
        system: str,
        user: str,
        *,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> ChatResult:
        data = await request_json(
            "POST",
            f"{BASE_URL}/messages",
            label=self.label,
            headers=self._headers,
            json_body={
                "model": model,
                "system": system,
                "messages": [{"role": "user", "content": user}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=timeout,
        )
        blocks = data.get("content")
        if not isinstance(blocks, list):
            raise MalformedResponseError("Anthropic returned an unexpected response shape.")
        text = "".join(
            str(b.get("text") or "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"
        ).strip()
        if not text:
            raise MalformedResponseError("Anthropic returned an empty response.")
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return ChatResult(
            text=text,
            usage=normalize_usage(usage.get("input_tokens"), usage.get("output_tokens")),
        )

    async def list_models(self) -> list[ModelInfo]:
        data = await request_json(
            "GET",
            f"{BASE_URL}/models",
            label=self.label,
            headers=self._headers,
            params={"limit": _MODELS_PAGE_LIMIT},
            timeout=METADATA_TIMEOUT_SECONDS,
        )
        models: list[ModelInfo] = []
        for item in data.get("data") or []:
            if not isinstance(item, dict):
                continue
            model_id = str(item.get("id") or "")
            if not model_id or len(model_id) > MODEL_ID_MAX_LENGTH:
                continue
            models.append(
                ModelInfo(
                    model_id=model_id,
                    display_name=str(item.get("display_name") or model_id)[:120],
                    capabilities=frozenset({CAPABILITY_CHAT, CAPABILITY_VISION}),
                )
            )
        return models

    async def test(self, model: str | None) -> None:
        await self.list_models()
