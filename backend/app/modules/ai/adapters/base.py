"""Vendor-neutral LLM adapter contracts, shared value types, and error hierarchy.

Domain services depend on these protocols only. Each vendor module in this package
implements them with a thin httpx client. Nothing here may log or echo API keys.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import httpx

CAPABILITY_CHAT = "chat"
CAPABILITY_EMBEDDING = "embedding"
CAPABILITY_VISION = "vision"

MODEL_ID_MAX_LENGTH = 80
MODEL_ID_PATTERN = r"^[A-Za-z0-9._:/-]{1,80}$"
# Model listing and connection tests should fail fast; chat uses the per-user timeout.
METADATA_TIMEOUT_SECONDS = 20.0
_VENDOR_MESSAGE_MAX_CHARS = 300


@dataclass(frozen=True)
class ProviderCredentials:
    api_key: str
    base_url: str | None = None


@dataclass(frozen=True)
class ChatResult:
    text: str
    # Normalized to {"prompt_tokens": int, "completion_tokens": int} when the vendor reports usage.
    usage: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelInfo:
    model_id: str
    display_name: str
    capabilities: frozenset[str]


class AiProviderError(Exception):
    """Base error for every vendor call. `code` is a stable, client-facing identifier."""

    code: str = "ai_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class MissingCredentialError(AiProviderError):
    code = "missing_credential"


class InvalidCredentialError(AiProviderError):
    code = "invalid_credential"


class ProviderUnavailableError(AiProviderError):
    code = "provider_unavailable"


class ProviderRequestError(ProviderUnavailableError):
    """Vendor rejected the request (4xx other than auth/rate limit), e.g. unknown model."""

    def __init__(self, message: str, *, status_code: int, vendor_message: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.vendor_message = vendor_message


class RateLimitError(AiProviderError):
    code = "rate_limit"


class ProviderTimeoutError(AiProviderError):
    code = "timeout"


class MalformedResponseError(AiProviderError):
    code = "malformed_response"


@runtime_checkable
class ChatCompletionProvider(Protocol):
    async def chat(
        self,
        system: str,
        user: str,
        *,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> ChatResult: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    async def embed(self, text: str, *, model: str) -> list[float]: ...


@runtime_checkable
class ProviderAdapter(ChatCompletionProvider, Protocol):
    """What every registered vendor adapter supports: chat, model listing, and a connection test."""

    label: str
    # False when the vendor has no model-listing API; users add model ids manually instead.
    supports_model_listing: bool

    async def list_models(self) -> list[ModelInfo]: ...

    async def test(self, model: str | None) -> None: ...


def _vendor_message(res: httpx.Response) -> str:
    """Extract the vendor's short error message (never the full body)."""
    try:
        data = res.json()
    except ValueError:
        return ""
    err = data.get("error") if isinstance(data, dict) else None
    message = err.get("message") if isinstance(err, dict) else err
    return str(message or "")[:_VENDOR_MESSAGE_MAX_CHARS]


async def request_json_value(
    method: str,
    url: str,
    *,
    label: str,
    headers: dict[str, str],
    timeout: float,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    """Perform one vendor HTTP call and map transport/status failures to AiProviderError.

    Returns the decoded JSON value (object or array).
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.request(method, url, headers=headers, json=json_body, params=params)
    except httpx.TimeoutException as exc:
        raise ProviderTimeoutError(f"{label} request timed out.") from exc
    except httpx.HTTPError as exc:
        raise ProviderUnavailableError(f"{label} is temporarily unavailable.") from exc

    if res.status_code in (401, 403):
        raise InvalidCredentialError(f"Invalid or revoked {label} API key. Check Integrations → AI.")
    if res.status_code == 429:
        raise RateLimitError(f"{label} rate limit reached. Try again in a moment.")
    if res.status_code >= 500:
        raise ProviderUnavailableError(f"{label} is temporarily unavailable.")
    if res.status_code >= 400:
        vendor_message = _vendor_message(res)
        suffix = f": {vendor_message}" if vendor_message else "."
        raise ProviderRequestError(
            f"{label} rejected the request (HTTP {res.status_code}){suffix}",
            status_code=res.status_code,
            vendor_message=vendor_message,
        )

    try:
        return res.json()
    except ValueError as exc:
        raise MalformedResponseError(f"{label} returned a non-JSON response.") from exc


async def request_json(
    method: str,
    url: str,
    *,
    label: str,
    headers: dict[str, str],
    timeout: float,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Like request_json_value, but the response must be a JSON object."""
    data = await request_json_value(
        method, url, label=label, headers=headers, timeout=timeout, json_body=json_body, params=params
    )
    if not isinstance(data, dict):
        raise MalformedResponseError(f"{label} returned an unexpected response shape.")
    return data


def normalize_usage(prompt_tokens: Any, completion_tokens: Any) -> dict[str, Any]:
    usage: dict[str, Any] = {}
    if isinstance(prompt_tokens, int):
        usage["prompt_tokens"] = prompt_tokens
    if isinstance(completion_tokens, int):
        usage["completion_tokens"] = completion_tokens
    return usage


def parse_json_object(raw: str) -> dict[str, Any]:
    """Tolerantly extract a JSON object from model output (strips fences, finds the outer braces)."""
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
