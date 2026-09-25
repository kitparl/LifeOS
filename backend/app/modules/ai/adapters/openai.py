"""OpenAI adapter (Chat Completions, Embeddings, Models). Also serves OpenAI-compatible base URLs."""

from __future__ import annotations

from typing import Any

from app.modules.ai.adapters.base import MalformedResponseError, ModelInfo, request_json
from app.modules.ai.adapters.openai_compatible import OpenAiCompatibleAdapter, has_marker, model_info

DEFAULT_BASE_URL = "https://api.openai.com/v1"
EMBED_TIMEOUT_SECONDS = 60.0

# On the official API, /v1/models also lists audio, image, and moderation models.
_CHAT_PREFIXES = ("gpt-", "chatgpt-", "o1", "o3", "o4", "ft:gpt-")
_NON_TEXT_MARKERS = ("-realtime", "-audio", "-transcribe", "-tts", "gpt-image", "-search")
_EMBEDDING_PREFIX = "text-embedding-"


class OpenAiAdapter(OpenAiCompatibleAdapter):
    label = "OpenAI"
    default_base_url = DEFAULT_BASE_URL
    max_tokens_field = "max_completion_tokens"

    def classify(self, model_id: str, item: dict[str, Any]) -> ModelInfo | None:
        if model_id.startswith(_EMBEDDING_PREFIX) or "embed" in model_id:
            return model_info(model_id, embedding=True)
        if self._base_url != DEFAULT_BASE_URL:
            # OpenAI-compatible servers use arbitrary ids; treat everything else as chat.
            return model_info(model_id)
        if not model_id.startswith(_CHAT_PREFIXES) or has_marker(model_id, _NON_TEXT_MARKERS):
            return None
        return model_info(model_id)

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
