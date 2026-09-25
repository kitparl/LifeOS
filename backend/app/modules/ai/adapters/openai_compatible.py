"""Shared adapter for vendors that expose OpenAI-style /chat/completions and /models.

Subclasses set `label`, `default_base_url` and, where needed, override `classify()` to decide
which listed models are chat or embedding models (returning None hides a model).
"""

from __future__ import annotations

from typing import Any

from app.modules.ai.adapters.base import (
    CAPABILITY_CHAT,
    CAPABILITY_EMBEDDING,
    METADATA_TIMEOUT_SECONDS,
    MODEL_ID_MAX_LENGTH,
    ChatResult,
    MalformedResponseError,
    ModelInfo,
    ProviderCredentials,
    ProviderRequestError,
    normalize_usage,
    request_json,
    request_json_value,
)

TEST_MAX_TOKENS = 16


class OpenAiCompatibleAdapter:
    label = "OpenAI-compatible"
    default_base_url = ""
    models_path = "/models"
    supports_model_listing = True
    model_list_validates_key = True
    # OpenAI itself uses max_completion_tokens; most compatible vendors still use max_tokens.
    max_tokens_field = "max_tokens"

    def __init__(self, credentials: ProviderCredentials):
        self._api_key = credentials.api_key
        self._base_url = (credentials.base_url or self.default_base_url).rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

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
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            self.max_tokens_field: max_tokens,
        }
        try:
            data = await self._post_chat(payload, timeout)
        except ProviderRequestError as exc:
            # Reasoning models only accept the default temperature; retry once without it.
            if exc.status_code != 400 or "temperature" not in exc.vendor_message:
                raise
            payload.pop("temperature")
            data = await self._post_chat(payload, timeout)

        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise MalformedResponseError(f"{self.label} returned an unexpected response shape.") from exc
        if not isinstance(text, str) or not text.strip():
            raise MalformedResponseError(f"{self.label} returned an empty response.")
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return ChatResult(
            text=text.strip(),
            usage=normalize_usage(usage.get("prompt_tokens"), usage.get("completion_tokens")),
        )

    async def _post_chat(self, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        return await request_json(
            "POST",
            f"{self._base_url}/chat/completions",
            label=self.label,
            headers=self._headers,
            json_body=payload,
            timeout=timeout,
        )

    async def list_models(self) -> list[ModelInfo]:
        if not self.supports_model_listing:
            return []
        data = await request_json_value(
            "GET",
            f"{self._base_url}{self.models_path}",
            label=self.label,
            headers=self._headers,
            timeout=METADATA_TIMEOUT_SECONDS,
        )
        items = data if isinstance(data, list) else (data.get("data") if isinstance(data, dict) else None)
        if not isinstance(items, list):
            raise MalformedResponseError(f"{self.label} returned an unexpected model list.")
        models: list[ModelInfo] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            model_id = str(item.get("id") or "")
            if not model_id or len(model_id) > MODEL_ID_MAX_LENGTH:
                continue
            info = self.classify(model_id, item)
            if info is not None:
                models.append(info)
        return sorted(models, key=lambda m: m.model_id)

    def classify(self, model_id: str, item: dict[str, Any]) -> ModelInfo | None:
        """Default: embedding models by name, everything else is chat."""
        return model_info(model_id, embedding="embed" in model_id)

    async def test(self, model: str | None) -> None:
        if self.supports_model_listing:
            # Listing models validates the key without spending tokens.
            await self.list_models()
            return
        if not model:
            raise MalformedResponseError(f"Add a {self.label} model id before testing the key.")
        await self.chat(
            "Reply with the single word: ok",
            "ok",
            model=model,
            temperature=0.2,
            max_tokens=TEST_MAX_TOKENS,
            timeout=METADATA_TIMEOUT_SECONDS,
        )


def model_info(
    model_id: str,
    *,
    embedding: bool = False,
    display_name: str | None = None,
    extra: frozenset[str] = frozenset(),
) -> ModelInfo:
    capability = CAPABILITY_EMBEDDING if embedding else CAPABILITY_CHAT
    return ModelInfo(
        model_id=model_id,
        display_name=(display_name or model_id)[:120],
        capabilities=frozenset({capability}) | extra,
    )


def has_marker(model_id: str, markers: tuple[str, ...]) -> bool:
    lowered = model_id.lower()
    return any(m in lowered for m in markers)

