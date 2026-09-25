"""OpenAI-compatible vendors: only base URL, model-list path, and model classification differ."""

from __future__ import annotations

from typing import Any

from app.modules.ai.adapters.base import CAPABILITY_VISION, ModelInfo
from app.modules.ai.adapters.openai_compatible import OpenAiCompatibleAdapter, has_marker, model_info


class GroqAdapter(OpenAiCompatibleAdapter):
    label = "Groq"
    default_base_url = "https://api.groq.com/openai/v1"
    _NON_CHAT = ("whisper", "tts", "guard")

    def classify(self, model_id: str, item: dict[str, Any]) -> ModelInfo | None:
        if item.get("active") is False or has_marker(model_id, self._NON_CHAT):
            return None
        return model_info(model_id)


class XaiAdapter(OpenAiCompatibleAdapter):
    label = "xAI"
    default_base_url = "https://api.x.ai/v1"
    _NON_CHAT = ("image", "video", "imagine")

    def classify(self, model_id: str, item: dict[str, Any]) -> ModelInfo | None:
        if has_marker(model_id, self._NON_CHAT):
            return None
        return model_info(model_id)


class DeepSeekAdapter(OpenAiCompatibleAdapter):
    label = "DeepSeek"
    default_base_url = "https://api.deepseek.com"


class MistralAdapter(OpenAiCompatibleAdapter):
    label = "Mistral"
    default_base_url = "https://api.mistral.ai/v1"

    def classify(self, model_id: str, item: dict[str, Any]) -> ModelInfo | None:
        if "embed" in model_id:
            return model_info(model_id, embedding=True)
        caps = item.get("capabilities") if isinstance(item.get("capabilities"), dict) else {}
        if caps.get("completion_chat") is False:
            return None
        extra = frozenset({CAPABILITY_VISION}) if caps.get("vision") else frozenset()
        return model_info(model_id, extra=extra)


class TogetherAdapter(OpenAiCompatibleAdapter):
    label = "Together AI"
    default_base_url = "https://api.together.xyz/v1"
    _CHAT_TYPES = frozenset({"chat", "language", "code"})

    def classify(self, model_id: str, item: dict[str, Any]) -> ModelInfo | None:
        model_type = str(item.get("type") or "")
        display_name = str(item.get("display_name") or "") or None
        if model_type == "embedding":
            return model_info(model_id, embedding=True, display_name=display_name)
        if model_type in self._CHAT_TYPES:
            return model_info(model_id, display_name=display_name)
        return None


class OpenRouterAdapter(OpenAiCompatibleAdapter):
    label = "OpenRouter"
    default_base_url = "https://openrouter.ai/api/v1"
    # Account-filtered list: honours the user's provider preferences, privacy settings, guardrails.
    models_path = "/models/user"

    def classify(self, model_id: str, item: dict[str, Any]) -> ModelInfo | None:
        arch = item.get("architecture") if isinstance(item.get("architecture"), dict) else {}
        outputs = arch.get("output_modalities")
        if isinstance(outputs, list) and outputs and "text" not in outputs:
            return None
        inputs = arch.get("input_modalities")
        extra = frozenset({CAPABILITY_VISION}) if isinstance(inputs, list) and "image" in inputs else frozenset()
        return model_info(model_id, display_name=str(item.get("name") or "") or None, extra=extra)


class PerplexityAdapter(OpenAiCompatibleAdapter):
    label = "Perplexity"
    default_base_url = "https://api.perplexity.ai"
    # No model-listing API: model ids are added manually (suggestions are seeded on first save).
    supports_model_listing = False
