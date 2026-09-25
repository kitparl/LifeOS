"""OpenAI adapter (Chat Completions, Embeddings, Models). Also serves OpenAI-compatible base URLs."""

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
)

DEFAULT_BASE_URL = "https://api.openai.com/v1"
EMBED_TIMEOUT_SECONDS = 60.0

# On the official API, /v1/models also lists audio, image, and moderation models.
_CHAT_PREFIXES = ("gpt-", "chatgpt-", "o1", "o3", "o4", "ft:gpt-")
_NON_TEXT_MARKERS = ("-realtime", "-audio", "-transcribe", "-tts", "gpt-image", "-search")
_EMBEDDING_PREFIX = "text-embedding-"


def _capabilities(model_id: str, *, official: bool) -> frozenset[str] | None:
    """Classify a listed model; None means it is not usable for text."""
    if model_id.startswith(_EMBEDDING_PREFIX) or "embed" in model_id:
        return frozenset({CAPABILITY_EMBEDDING})
    if not official:
        # OpenAI-compatible servers use arbitrary ids; treat everything else as chat.
        return frozenset({CAPABILITY_CHAT})
    if not model_id.startswith(_CHAT_PREFIXES):
        return None
    if any(marker in model_id for marker in _NON_TEXT_MARKERS):
        return None
    return frozenset({CAPABILITY_CHAT})


class OpenAiAdapter:
    label = "OpenAI"

    def __init__(self, credentials: ProviderCredentials):
        self._api_key = credentials.api_key
        self._base_url = (credentials.base_url or DEFAULT_BASE_URL).rstrip("/")

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
            "max_completion_tokens": max_tokens,
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
            raise MalformedResponseError("OpenAI returned an unexpected response shape.") from exc
        if not isinstance(text, str) or not text.strip():
            raise MalformedResponseError("OpenAI returned an empty response.")
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

    async def embed(self, text: str, *, model: str) -> list[float]:
        data = await request_json(
            "POST",
            f"{self._base_url}/embeddings",
            label=self.label,
            headers=self._headers,
            json_body={"model": model, "input": text},
            timeout=EMBED_TIMEOUT_SECONDS,
        )
        try:
            vector = data["data"][0]["embedding"]
        except (KeyError, IndexError, TypeError) as exc:
            raise MalformedResponseError("OpenAI returned an unexpected embedding shape.") from exc
        if not isinstance(vector, list):
            raise MalformedResponseError("OpenAI returned an unexpected embedding shape.")
        return vector

    async def list_models(self) -> list[ModelInfo]:
        data = await request_json(
            "GET",
            f"{self._base_url}/models",
            label=self.label,
            headers=self._headers,
            timeout=METADATA_TIMEOUT_SECONDS,
        )
        official = self._base_url == DEFAULT_BASE_URL
        models: list[ModelInfo] = []
        for item in data.get("data") or []:
            model_id = str(item.get("id") or "") if isinstance(item, dict) else ""
            if not model_id or len(model_id) > MODEL_ID_MAX_LENGTH:
                continue
            caps = _capabilities(model_id, official=official)
            if caps is not None:
                models.append(ModelInfo(model_id=model_id, display_name=model_id, capabilities=caps))
        return sorted(models, key=lambda m: m.model_id)

    async def test(self, model: str | None) -> None:
        # Listing models validates the key without spending tokens.
        await self.list_models()
