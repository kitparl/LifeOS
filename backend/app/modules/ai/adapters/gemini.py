"""Google Gemini adapter (Generative Language API, AI Studio key)."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from app.modules.ai.adapters.base import (
    CAPABILITY_CHAT,
    CAPABILITY_EMBEDDING,
    METADATA_TIMEOUT_SECONDS,
    MODEL_ID_MAX_LENGTH,
    ChatResult,
    InvalidCredentialError,
    MalformedResponseError,
    ModelInfo,
    ProviderCredentials,
    ProviderRequestError,
    normalize_usage,
    request_json,
)

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_MODEL_PREFIX = "models/"
_MODELS_PAGE_SIZE = 1000
_MAX_MODEL_PAGES = 5


class GeminiAdapter:
    label = "Gemini"
    supports_model_listing = True

    def __init__(self, credentials: ProviderCredentials):
        self._api_key = credentials.api_key

    async def _request(self, method: str, path: str, *, timeout: float, **kwargs: Any) -> dict[str, Any]:
        try:
            return await request_json(
                method,
                f"{BASE_URL}/{path}",
                label=self.label,
                # Header, not ?key=, so the key never lands in URLs or access logs.
                headers={"x-goog-api-key": self._api_key},
                timeout=timeout,
                **kwargs,
            )
        except ProviderRequestError as exc:
            # Gemini reports a bad key as 400 INVALID_ARGUMENT rather than 401/403.
            if exc.status_code == 400 and "API key" in exc.vendor_message:
                raise InvalidCredentialError(
                    "Invalid or revoked Gemini API key. Check Integrations → AI."
                ) from exc
            raise

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
        data = await self._request(
            "POST",
            f"models/{quote(model, safe='.-_')}:generateContent",
            timeout=timeout,
            json_body={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
            },
        )
        try:
            candidate = data["candidates"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise MalformedResponseError("Gemini returned no candidates.") from exc
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(str(p.get("text") or "") for p in parts if isinstance(p, dict)).strip()
        if not text:
            reason = candidate.get("finishReason") or "unknown"
            raise MalformedResponseError(f"Gemini returned no text (finish reason: {reason}).")
        usage = data.get("usageMetadata") if isinstance(data.get("usageMetadata"), dict) else {}
        return ChatResult(
            text=text,
            usage=normalize_usage(usage.get("promptTokenCount"), usage.get("candidatesTokenCount")),
        )

    async def list_models(self) -> list[ModelInfo]:
        models: list[ModelInfo] = []
        page_token: str | None = None
        for _ in range(_MAX_MODEL_PAGES):
            params: dict[str, Any] = {"pageSize": _MODELS_PAGE_SIZE}
            if page_token:
                params["pageToken"] = page_token
            data = await self._request("GET", "models", timeout=METADATA_TIMEOUT_SECONDS, params=params)
            for item in data.get("models") or []:
                info = _to_model_info(item)
                if info is not None:
                    models.append(info)
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return models

    async def test(self, model: str | None) -> None:
        await self._request(
            "GET", "models", timeout=METADATA_TIMEOUT_SECONDS, params={"pageSize": 1}
        )


def _to_model_info(item: Any) -> ModelInfo | None:
    if not isinstance(item, dict):
        return None
    name = str(item.get("name") or "")
    model_id = name[len(_MODEL_PREFIX):] if name.startswith(_MODEL_PREFIX) else name
    if not model_id or len(model_id) > MODEL_ID_MAX_LENGTH:
        return None
    methods = item.get("supportedGenerationMethods") or []
    caps: set[str] = set()
    if "generateContent" in methods:
        caps.add(CAPABILITY_CHAT)
    if "embedContent" in methods:
        caps.add(CAPABILITY_EMBEDDING)
    if not caps:
        return None
    return ModelInfo(
        model_id=model_id,
        display_name=str(item.get("displayName") or model_id)[:120],
        capabilities=frozenset(caps),
    )
