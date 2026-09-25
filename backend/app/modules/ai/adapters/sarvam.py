"""Sarvam adapter (Chat Completions).

Sarvam does not publish a model-listing endpoint, so `list_models` returns a seeded
list; users can still enter any newer model id as a custom model.
"""

from __future__ import annotations

from app.modules.ai.adapters.base import (
    CAPABILITY_CHAT,
    METADATA_TIMEOUT_SECONDS,
    ChatResult,
    MalformedResponseError,
    ModelInfo,
    ProviderCredentials,
    normalize_usage,
    request_json,
)

CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
DEFAULT_MODEL = "sarvam-105b"
SEEDED_MODELS: tuple[ModelInfo, ...] = (
    ModelInfo(model_id=DEFAULT_MODEL, display_name=DEFAULT_MODEL, capabilities=frozenset({CAPABILITY_CHAT})),
)


class SarvamAdapter:
    label = "Sarvam"

    def __init__(self, credentials: ProviderCredentials):
        self._api_key = credentials.api_key

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
            CHAT_URL,
            label=self.label,
            headers={"api-subscription-key": self._api_key},
            json_body={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "n": 1,
                "stream": False,
                "reasoning_effort": None,
            },
            timeout=timeout,
        )
        try:
            text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise MalformedResponseError("Sarvam returned an unexpected response shape.") from exc
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return ChatResult(
            text=text,
            usage=normalize_usage(usage.get("prompt_tokens"), usage.get("completion_tokens")),
        )

    async def list_models(self) -> list[ModelInfo]:
        return list(SEEDED_MODELS)

    async def test(self, model: str | None) -> None:
        # No listing endpoint: a minimal chat call is the only way to validate the key.
        await self.chat(
            "Reply with the single word: ok",
            "ok",
            model=model or DEFAULT_MODEL,
            temperature=0.2,
            max_tokens=8,
            timeout=METADATA_TIMEOUT_SECONDS,
        )
