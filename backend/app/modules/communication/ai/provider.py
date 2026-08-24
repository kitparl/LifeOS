"""AI writing provider protocol and Sarvam adapter."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Protocol, runtime_checkable

import httpx

from app.modules.communication.ai.rubric import (
    DIMENSIONS,
    EVALUATION_VERSION,
    PROMPT_VERSION,
    REWRITE_PROMPT_VERSION,
    RUBRIC_VERSION,
    compute_overall_score,
    normalize_dimensions,
)

logger = logging.getLogger(__name__)

SARVAM_CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
DEFAULT_MODEL = "sarvam-105b"
MAX_CONTENT_CHARS = 12_000
MAX_TOKENS = 1200
REWRITE_MAX_TOKENS = 1400
TEMPERATURE = 0.25


class WritingAiError(Exception):
    """Base error for writing AI operations."""

    code: str = "ai_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class MissingCredentialError(WritingAiError):
    code = "missing_credential"


class InvalidCredentialError(WritingAiError):
    code = "invalid_credential"


class ProviderUnavailableError(WritingAiError):
    code = "provider_unavailable"


class RateLimitError(WritingAiError):
    code = "rate_limit"


class TimeoutError_(WritingAiError):
    code = "timeout"


class MalformedResponseError(WritingAiError):
    code = "malformed_response"


@runtime_checkable
class AIWritingProvider(Protocol):
    async def evaluate_writing(
        self,
        *,
        title: str,
        content: str,
        category: str,
    ) -> dict[str, Any]: ...


class SarvamWritingProvider:
    """httpx adapter for Sarvam Chat Completions (sarvam-105b)."""

    def __init__(self, api_key: str, *, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def evaluate_writing(
        self,
        *,
        title: str,
        content: str,
        category: str,
    ) -> dict[str, Any]:
        if not self.enabled:
            raise MissingCredentialError(
                "Connect your Sarvam API key in Integrations before requesting AI Feedback."
            )

        truncated = False
        body = content or ""
        if len(body) > MAX_CONTENT_CHARS:
            body = body[:MAX_CONTENT_CHARS]
            truncated = True

        system = _build_system_prompt()
        user_msg = (
            f"Title: {title}\nCategory: {category}\n\nWriting:\n{body}\n\n"
            "Return ONLY the JSON object described in the system prompt."
        )

        raw_text, usage = await self._chat(system, user_msg)
        parsed = _parse_json_object(raw_text)
        validated = _validate_canonical(parsed, provider="sarvam", model=self.model)
        if truncated:
            validated["truncated"] = True
            validated["truncationNote"] = (
                f"Feedback is based on the first {MAX_CONTENT_CHARS} characters of the writing."
            )
        validated["_usage"] = usage
        return validated

    async def suggest_rewrite(
        self,
        *,
        title: str,
        content: str,
        category: str,
    ) -> dict[str, Any]:
        truncated = False
        body = content or ""
        if len(body) > MAX_CONTENT_CHARS:
            body = body[:MAX_CONTENT_CHARS]
            truncated = True

        system = _build_rewrite_system_prompt()
        user_msg = (
            f"Title: {title}\nCategory: {category}\n\nOriginal writing:\n{body}\n\n"
            "Return ONLY the JSON object described in the system prompt."
        )

        raw_text, usage = await self._chat(
            system, user_msg, max_tokens=REWRITE_MAX_TOKENS, temperature=0.35
        )
        parsed = _parse_json_object(raw_text)
        validated = _validate_rewrite(parsed, provider="sarvam", model=self.model)
        if truncated:
            validated["truncated"] = True
            validated["truncationNote"] = (
                f"Rewrite is based on the first {MAX_CONTENT_CHARS} characters of the writing."
            )
        validated["_usage"] = usage
        return validated

    async def _chat(
        self,
        system: str,
        user_message: str,
        *,
        max_tokens: int = MAX_TOKENS,
        temperature: float = TEMPERATURE,
    ) -> tuple[str, dict[str, Any]]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "n": 1,
            "stream": False,
            "reasoning_effort": None,
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(
                    SARVAM_CHAT_URL,
                    headers={
                        "api-subscription-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise TimeoutError_("Sarvam request timed out. Your writing was not changed.") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                "AI feedback is temporarily unavailable. Your writing has not been changed."
            ) from exc

        if res.status_code == 403:
            raise InvalidCredentialError(
                "Invalid or revoked Sarvam API key. Check Integrations → Sarvam."
            )
        if res.status_code == 429:
            raise RateLimitError("Sarvam rate limit reached. Try again in a moment.")
        if res.status_code >= 500:
            raise ProviderUnavailableError(
                "AI feedback is temporarily unavailable. Your writing has not been changed."
            )
        if res.status_code >= 400:
            raise ProviderUnavailableError(f"Sarvam returned HTTP {res.status_code}.")

        data = res.json()
        try:
            text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise MalformedResponseError("Sarvam returned an unexpected response shape.") from exc

        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return text, usage


def _build_system_prompt() -> str:
    dims = ", ".join(DIMENSIONS)
    return (
        "You are a writing coach. Evaluate the user's writing honestly. "
        "Do NOT invent problems when writing is already strong. "
        "Do NOT rewrite the writing. "
        f"Score each dimension 0-100: {dims}. "
        "Respond with ONLY valid JSON (no markdown fences) matching this shape:\n"
        "{\n"
        '  "dimensions": { "<dimension>": <0-100>, ... },\n'
        '  "strengths": ["..."],\n'
        '  "issues": [{"location":"","problem_type":"","severity":"low|medium|high",'
        '"original_text":"","explanation":"","suggestion":""}],\n'
        '  "suggestions": ["..."],\n'
        '  "alreadyStrong": false\n'
        "}\n"
        "If alreadyStrong is true, issues and suggestions may be empty."
    )


def _build_rewrite_system_prompt() -> str:
    return (
        "You are an expert writing coach. The user wants to see how YOU would write their piece "
        "if you were the author — same intent, audience, and tone, but clearer and more polished. "
        "Do NOT change the core message or invent new facts. "
        "Respond with ONLY valid JSON (no markdown fences) matching this shape:\n"
        "{\n"
        '  "suggestedVersion": "<full rewritten text>",\n'
        '  "whyBetter": ["short reason 1", "..."],\n'
        '  "keyChanges": ["specific change 1", "..."]\n'
        "}\n"
        "Keep whyBetter and keyChanges concise (max 6 items each)."
    )


def _validate_rewrite(data: dict, *, provider: str, model: str) -> dict[str, Any]:
    suggested = str(data.get("suggestedVersion") or data.get("suggested_version") or "").strip()
    if not suggested:
        raise MalformedResponseError("AI rewrite response did not include suggestedVersion.")

    why_raw = data.get("whyBetter") or data.get("why_better") or []
    if not isinstance(why_raw, list):
        why_raw = []
    why_better = [str(x).strip() for x in why_raw if str(x).strip()][:6]

    changes_raw = data.get("keyChanges") or data.get("key_changes") or []
    if not isinstance(changes_raw, list):
        changes_raw = []
    key_changes = [str(x).strip() for x in changes_raw if str(x).strip()][:6]

    return {
        "promptVersion": REWRITE_PROMPT_VERSION,
        "provider": provider,
        "model": model,
        "suggestedVersion": suggested[:20_000],
        "whyBetter": why_better,
        "keyChanges": key_changes,
    }


def _parse_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise MalformedResponseError("AI response did not contain a JSON object.")
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise MalformedResponseError("AI response JSON could not be parsed.") from exc
    if not isinstance(data, dict):
        raise MalformedResponseError("AI response JSON was not an object.")
    return data


def _validate_canonical(data: dict, *, provider: str, model: str) -> dict[str, Any]:
    dimensions = normalize_dimensions(data.get("dimensions") or {})
    overall = compute_overall_score(dimensions)

    strengths = data.get("strengths") or []
    if not isinstance(strengths, list):
        strengths = []
    strengths = [str(s).strip() for s in strengths if str(s).strip()][:20]

    suggestions = data.get("suggestions") or []
    if not isinstance(suggestions, list):
        suggestions = []
    suggestions = [str(s).strip() for s in suggestions if str(s).strip()][:20]

    issues_raw = data.get("issues") or []
    if not isinstance(issues_raw, list):
        issues_raw = []
    issues: list[dict[str, str]] = []
    for item in issues_raw[:40]:
        if not isinstance(item, dict):
            continue
        severity = str(item.get("severity") or "medium").lower()
        if severity not in ("low", "medium", "high"):
            severity = "medium"
        issues.append(
            {
                "location": str(item.get("location") or "")[:200],
                "problem_type": str(item.get("problem_type") or "")[:80],
                "severity": severity,
                "original_text": str(item.get("original_text") or "")[:500],
                "explanation": str(item.get("explanation") or "")[:1000],
                "suggestion": str(item.get("suggestion") or "")[:1000],
            }
        )

    already_strong = bool(data.get("alreadyStrong"))
    if overall >= 92 and not issues:
        already_strong = True

    return {
        "evaluationVersion": EVALUATION_VERSION,
        "rubricVersion": RUBRIC_VERSION,
        "promptVersion": PROMPT_VERSION,
        "provider": provider,
        "model": model,
        "overallScore": overall,
        "dimensions": dimensions,
        "strengths": strengths,
        "issues": issues,
        "suggestions": suggestions,
        "alreadyStrong": already_strong,
    }
