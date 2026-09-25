"""AI writing provider protocol and the chat-backed implementation used for every vendor."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.modules.ai.adapters.base import (
    ChatCompletionProvider,
    ChatResult,
    MalformedResponseError,
    parse_json_object,
)
from app.modules.communication.ai.rubric import (
    DIMENSIONS,
    EVALUATION_VERSION,
    PROMPT_VERSION,
    REWRITE_PROMPT_VERSION,
    RUBRIC_VERSION,
    compute_overall_score,
    normalize_dimensions,
)

MAX_CONTENT_CHARS = 12_000
MAX_TOKENS = 1200
REWRITE_MAX_TOKENS = 1400
TEMPERATURE = 0.25
REWRITE_TEMPERATURE = 0.35


@runtime_checkable
class AIWritingProvider(Protocol):
    async def evaluate_writing(
        self,
        *,
        title: str,
        content: str,
        category: str,
    ) -> dict[str, Any]: ...

    async def suggest_rewrite(
        self,
        *,
        title: str,
        content: str,
        category: str,
    ) -> dict[str, Any]: ...


def _truncate(content: str) -> tuple[str, bool]:
    body = content or ""
    if len(body) > MAX_CONTENT_CHARS:
        return body[:MAX_CONTENT_CHARS], True
    return body, False


class ChatWritingProvider:
    """Implements AIWritingProvider on top of any vendor chat adapter.

    Rubric prompts and canonical validation live here, so every vendor produces the
    same evaluation/rewrite shape.
    """

    def __init__(self, chat: ChatCompletionProvider, *, provider: str, model: str, timeout: float):
        self.chat = chat
        self.provider = provider
        self.model = model
        self.timeout = timeout

    async def evaluate_writing(
        self,
        *,
        title: str,
        content: str,
        category: str,
    ) -> dict[str, Any]:
        body, truncated = _truncate(content)
        user_msg = (
            f"Title: {title}\nCategory: {category}\n\nWriting:\n{body}\n\n"
            "Return ONLY the JSON object described in the system prompt."
        )
        result = await self._chat(_build_system_prompt(), user_msg, max_tokens=MAX_TOKENS, temperature=TEMPERATURE)
        validated = _validate_canonical(parse_json_object(result.text), provider=self.provider, model=self.model)
        if truncated:
            validated["truncated"] = True
            validated["truncationNote"] = (
                f"Feedback is based on the first {MAX_CONTENT_CHARS} characters of the writing."
            )
        validated["_usage"] = result.usage
        return validated

    async def suggest_rewrite(
        self,
        *,
        title: str,
        content: str,
        category: str,
    ) -> dict[str, Any]:
        body, truncated = _truncate(content)
        user_msg = (
            f"Title: {title}\nCategory: {category}\n\nOriginal writing:\n{body}\n\n"
            "Return ONLY the JSON object described in the system prompt."
        )
        result = await self._chat(
            _build_rewrite_system_prompt(), user_msg, max_tokens=REWRITE_MAX_TOKENS, temperature=REWRITE_TEMPERATURE
        )
        validated = _validate_rewrite(parse_json_object(result.text), provider=self.provider, model=self.model)
        if truncated:
            validated["truncated"] = True
            validated["truncationNote"] = (
                f"Rewrite is based on the first {MAX_CONTENT_CHARS} characters of the writing."
            )
        validated["_usage"] = result.usage
        return validated

    async def _chat(self, system: str, user_message: str, *, max_tokens: int, temperature: float) -> ChatResult:
        return await self.chat.chat(
            system,
            user_message,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=self.timeout,
        )


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
