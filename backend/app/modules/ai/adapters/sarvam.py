"""Sarvam adapter (Chat Completions + public model lists).

Sarvam serves two OpenAI-style API versions:
- v1: Sarvam's own models (`sarvam-105b`, `sarvam-105b-conversations`), `GET /v1/models`
- v2: adds open-weight models (e.g. `glm5.3`, `gemma4`, `deepseekv4-flash`), `GET /v2/models`

Both lists are public (same for every caller), so listing does not validate a key; the
connection test makes a minimal chat call instead.
"""

from __future__ import annotations

from app.modules.ai.adapters.base import (
    CAPABILITY_CHAT,
    METADATA_TIMEOUT_SECONDS,
    MODEL_ID_MAX_LENGTH,
    ChatResult,
    MalformedResponseError,
    ModelInfo,
    ProviderCredentials,
    normalize_usage,
    request_json,
)

BASE_URL = "https://api.sarvam.ai"
DEFAULT_MODEL = "sarvam-105b"
# Sarvam's own models stay on v1 (unchanged behaviour); open-weight models are only served on v2.
_V1_MODEL_PREFIX = "sarvam-"
_API_VERSIONS = ("v1", "v2")


def api_version_for(model: str) -> str:
    return "v1" if model.startswith(_V1_MODEL_PREFIX) else "v2"


class SarvamAdapter:
    label = "Sarvam"
    supports_model_listing = True
    model_list_validates_key = False

    def __init__(self, credentials: ProviderCredentials):
        self._api_key = credentials.api_key

    @property
    def _headers(self) -> dict[str, str]:
        return {"api-subscription-key": self._api_key}

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
            f"{BASE_URL}/{api_version_for(model)}/chat/completions",
            label=self.label,
            headers=self._headers,
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
        """Merge the v1 and v2 lists (a model served on both appears once)."""
        seen: dict[str, ModelInfo] = {}
        for version in _API_VERSIONS:
            data = await request_json(
                "GET",
                f"{BASE_URL}/{version}/models",
                label=self.label,
                headers=self._headers,
                timeout=METADATA_TIMEOUT_SECONDS,
            )
            for item in data.get("data") or []:
                model_id = str(item.get("id") or "") if isinstance(item, dict) else ""
                if model_id and len(model_id) <= MODEL_ID_MAX_LENGTH and model_id not in seen:
                    seen[model_id] = ModelInfo(
                        model_id=model_id, display_name=model_id, capabilities=frozenset({CAPABILITY_CHAT})
                    )
        return sorted(seen.values(), key=lambda m: m.model_id)

    async def test(self, model: str | None) -> None:
        # The model lists are public, so only a real (minimal) chat call validates the key.
        await self.chat(
            "Reply with the single word: ok",
            "ok",
            model=model or DEFAULT_MODEL,
            temperature=0.2,
            max_tokens=8,
            timeout=METADATA_TIMEOUT_SECONDS,
        )
