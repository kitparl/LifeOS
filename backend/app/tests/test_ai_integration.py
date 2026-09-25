"""AI Integration: provider BYOK config, dynamic model catalogs, adapter registry/gateway,
use-case selection, and every migrated call site. All vendor HTTP is mocked."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from unittest.mock import patch

import httpx
import pytest
from app.core.config import get_settings
from app.core.crypto import encrypt
from app.modules.ai.adapters import base as adapter_base
from app.modules.ai.adapters.base import (
    CAPABILITY_CHAT,
    CAPABILITY_EMBEDDING,
    InvalidCredentialError,
    MissingCredentialError,
    ProviderCredentials,
    ProviderRequestError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)
from app.modules.ai.adapters.gemini import GeminiAdapter
from app.modules.ai.adapters.openai import OpenAiAdapter
from app.modules.ai.adapters.registry import AI_PROVIDERS, get_adapter
from app.modules.ai.gateway import AiGateway
from app.modules.ai.use_cases import USE_CASE_RAG_CHAT, USE_CASE_WRITING_FEEDBACK
from app.modules.analytics_dashboard.cache import analytics_cache
from app.modules.integrations.ai.config import load_config, mask_config, parse_config, serialize_config

API = "/api/v1"
DIMENSIONS = (
    "grammar", "punctuation", "spelling", "clarity", "readability", "vocabulary", "sentenceVariety",
    "coherence", "structure", "conciseness", "tone", "intentAlignment", "audienceAppropriateness",
)
EVALUATION_JSON = json.dumps(
    {
        "dimensions": {d: 80 for d in DIMENSIONS},
        "strengths": ["Clear"],
        "issues": [],
        "suggestions": ["Vary sentences"],
        "alreadyStrong": False,
    }
)
REWRITE_JSON = json.dumps(
    {"suggestedVersion": "He went to school yesterday.", "whyBetter": ["Tense"], "keyChanges": ["go → went"]}
)


# ---------------------------------------------------------------------------
# Fake vendor HTTP
# ---------------------------------------------------------------------------


class FakeVendors:
    """Routes adapter requests by host/path and records them for assertions."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.chat_text = "Mocked reply"
        self.status: dict[str, int] = {}  # host -> forced status code

    def bodies(self, host: str) -> list[dict]:
        return [json.loads(r.content) for r in self.requests if r.url.host == host and r.content]

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        host, path = request.url.host, request.url.path
        if host in self.status:
            return httpx.Response(self.status[host], json={"error": {"message": "forced"}})
        if host == "api.openai.com":
            if path == "/v1/models":
                return httpx.Response(
                    200,
                    json={
                        "data": [
                            {"id": "gpt-4o-mini"},
                            {"id": "o3-mini"},
                            {"id": "text-embedding-3-small"},
                            {"id": "whisper-1"},
                            {"id": "dall-e-3"},
                            {"id": "gpt-4o-realtime-preview"},
                        ]
                    },
                )
            if path == "/v1/chat/completions":
                return httpx.Response(
                    200,
                    json={
                        "choices": [{"message": {"content": self.chat_text}}],
                        "usage": {"prompt_tokens": 11, "completion_tokens": 7},
                    },
                )
            if path == "/v1/embeddings":
                return httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2, 0.3]}]})
        if host == "api.anthropic.com":
            if path == "/v1/models":
                return httpx.Response(
                    200,
                    json={"data": [{"id": "claude-opus-5-5", "display_name": "Claude Opus 5.5"}]},
                )
            if path == "/v1/messages":
                return httpx.Response(
                    200,
                    json={
                        "content": [{"type": "text", "text": self.chat_text}],
                        "usage": {"input_tokens": 9, "output_tokens": 4},
                    },
                )
        if host == "generativelanguage.googleapis.com":
            if path == "/v1beta/models":
                return httpx.Response(
                    200,
                    json={
                        "models": [
                            {
                                "name": "models/gemini-2.5-flash",
                                "displayName": "Gemini 2.5 Flash",
                                "supportedGenerationMethods": ["generateContent"],
                            },
                            {"name": "models/text-embedding-004", "supportedGenerationMethods": ["embedContent"]},
                            {"name": "models/aqa", "supportedGenerationMethods": ["generateAnswer"]},
                        ]
                    },
                )
            if path.endswith(":generateContent"):
                return httpx.Response(
                    200,
                    json={
                        "candidates": [{"content": {"parts": [{"text": self.chat_text}]}}],
                        "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 3},
                    },
                )
        if path.endswith("/chat/completions") and host in COMPATIBLE_HOSTS | {"api.sarvam.ai"}:
            return httpx.Response(200, json={"choices": [{"message": {"content": self.chat_text}}]})
        if host in VENDOR_MODEL_LISTS and path == VENDOR_MODEL_LISTS[host][0]:
            return httpx.Response(200, json=VENDOR_MODEL_LISTS[host][1])
        return httpx.Response(404, json={"error": {"message": f"unrouted {host}{path}"}})


# host -> (model-list path, raw vendor response). Covers each vendor's classification rules.
VENDOR_MODEL_LISTS: dict[str, tuple[str, object]] = {
    "api.groq.com": (
        "/openai/v1/models",
        {"data": [{"id": "llama-3.3-70b-versatile", "active": True}, {"id": "whisper-large-v3"},
                  {"id": "old-model", "active": False}, {"id": "llama-guard-4-12b"}]},
    ),
    "api.x.ai": ("/v1/models", {"data": [{"id": "grok-4"}, {"id": "grok-2-image"}]}),
    "api.deepseek.com": ("/models", {"object": "list", "data": [{"id": "deepseek-chat"}, {"id": "deepseek-reasoner"}]}),
    "api.mistral.ai": (
        "/v1/models",
        {"data": [{"id": "mistral-large-latest", "capabilities": {"completion_chat": True, "vision": True}},
                  {"id": "mistral-embed", "capabilities": {"completion_chat": False}},
                  {"id": "codestral-fim", "capabilities": {"completion_chat": False}}]},
    ),
    "api.together.xyz": (
        "/v1/models",
        [{"id": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "type": "chat", "display_name": "Llama 3.3 70B"},
         {"id": "BAAI/bge-large-en-v1.5", "type": "embedding"}, {"id": "black-forest-labs/FLUX.1", "type": "image"}],
    ),
    "openrouter.ai": (
        "/api/v1/models/user",
        {"data": [{"id": "anthropic/claude-opus-5", "name": "Claude Opus 5",
                   "architecture": {"input_modalities": ["text", "image"], "output_modalities": ["text"]}},
                  {"id": "openai/gpt-image-1", "architecture": {"output_modalities": ["image"]}}]},
    ),
}
COMPATIBLE_HOSTS = frozenset(VENDOR_MODEL_LISTS) | {"api.perplexity.ai"}


@contextmanager
def mock_vendor_http(handler: Callable[[httpx.Request], httpx.Response]) -> Iterator[None]:
    real_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    with patch.object(adapter_base.httpx, "AsyncClient", side_effect=factory):
        yield


@pytest.fixture
def vendors() -> Iterator[FakeVendors]:
    fake = FakeVendors()
    with mock_vendor_http(fake):
        yield fake


async def _auth(client, email: str) -> dict[str, str]:
    reg = await client.post(
        f"{API}/auth/register",
        json={
            "username": "usr_" + email.split("@")[0].replace(".", "")[:26],
            "email": email,
            "password": "password123",
            "display_name": "AI Integration",
        },
    )
    assert reg.status_code in (200, 201), reg.text
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


async def _connect(client, headers, provider: str, key: str, **extra) -> dict:
    res = await client.put(
        f"{API}/integrations/ai/{provider}/config", headers=headers, json={"api_key": key, **extra}
    )
    assert res.status_code == 200, res.text
    return res.json()


async def _user_id(client, headers) -> str:
    return (await client.get(f"{API}/auth/me", headers=headers)).json()["id"]


# ---------------------------------------------------------------------------
# Config (encrypt / mask / legacy Sarvam rows)
# ---------------------------------------------------------------------------


def test_config_roundtrip_mask_and_keep_blank_key():
    raw = "sk-live-abcdef-7788"
    first = serialize_config(existing_json=None, api_key=raw, default_model="gpt-4o-mini", base_url=None)
    assert raw not in first
    cfg = parse_config(first)
    assert cfg is not None and cfg.api_key == raw and cfg.default_model == "gpt-4o-mini"

    kept = serialize_config(existing_json=first, api_key="  ", default_model=None, base_url=None)
    assert parse_config(kept).api_key == raw
    assert parse_config(kept).default_model is None

    masked = mask_config(first)
    assert masked.configured and masked.api_key_masked == "****7788"


def test_legacy_sarvam_rows_parse_unchanged():
    legacy_encrypted = json.dumps({"api_key_enc": encrypt("sarvam-legacy-1234")})
    assert parse_config(legacy_encrypted).api_key == "sarvam-legacy-1234"
    assert parse_config(legacy_encrypted).default_model is None
    legacy_plain = json.dumps({"api_key": "plain-5678"})
    assert parse_config(legacy_plain).api_key == "plain-5678"
    assert parse_config(None) is None
    assert load_config("not json").api_key == ""


# ---------------------------------------------------------------------------
# Adapters: model listing + error mapping
# ---------------------------------------------------------------------------


async def test_openai_list_models_filters_and_flags(vendors):
    models = {m.model_id: m for m in await OpenAiAdapter(ProviderCredentials("k")).list_models()}
    assert set(models) == {"gpt-4o-mini", "o3-mini", "text-embedding-3-small"}
    assert models["gpt-4o-mini"].capabilities == {CAPABILITY_CHAT}
    assert models["text-embedding-3-small"].capabilities == {CAPABILITY_EMBEDDING}


async def test_openai_compatible_base_url_keeps_arbitrary_ids():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "llm.example.com"
        return httpx.Response(200, json={"data": [{"id": "llama-3-70b"}, {"id": "nomic-embed-text"}]})

    with mock_vendor_http(handler):
        adapter = OpenAiAdapter(ProviderCredentials("k", base_url="https://llm.example.com/v1"))
        models = {m.model_id: m.capabilities for m in await adapter.list_models()}
    assert models == {"llama-3-70b": {CAPABILITY_CHAT}, "nomic-embed-text": {CAPABILITY_EMBEDDING}}


async def test_gemini_list_models_strips_prefix_and_keeps_key_out_of_url(vendors):
    models = {m.model_id: m.capabilities for m in await GeminiAdapter(ProviderCredentials("g-key")).list_models()}
    assert models == {"gemini-2.5-flash": {CAPABILITY_CHAT}, "text-embedding-004": {CAPABILITY_EMBEDDING}}
    req = vendors.requests[-1]
    assert "g-key" not in str(req.url)
    assert req.headers["x-goog-api-key"] == "g-key"


async def test_anthropic_chat_uses_top_level_system_and_normalizes_usage(vendors):
    adapter = get_adapter("anthropic", ProviderCredentials("a-key"))
    result = await adapter.chat("SYS", "hello", model="claude-opus-5-5", temperature=0.2, max_tokens=50, timeout=5)
    assert result.text == "Mocked reply"
    assert result.usage == {"prompt_tokens": 9, "completion_tokens": 4}
    body = vendors.bodies("api.anthropic.com")[-1]
    assert body["system"] == "SYS" and body["messages"] == [{"role": "user", "content": "hello"}]
    assert vendors.requests[-1].headers["x-api-key"] == "a-key"


@pytest.mark.parametrize(
    "status,error",
    [
        (401, InvalidCredentialError),
        (403, InvalidCredentialError),
        (429, RateLimitError),
        (503, ProviderUnavailableError),
        (404, ProviderRequestError),
    ],
)
async def test_http_status_mapping(status, error):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": {"message": "model not found"}})

    with mock_vendor_http(handler), pytest.raises(error) as exc_info:
        await OpenAiAdapter(ProviderCredentials("sk-secret-key")).list_models()
    assert "sk-secret-key" not in str(exc_info.value)


async def test_timeout_and_gemini_bad_key_mapping():
    def timeout(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    with mock_vendor_http(timeout), pytest.raises(ProviderTimeoutError):
        await OpenAiAdapter(ProviderCredentials("k")).list_models()

    def bad_key(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"message": "API key not valid. Please pass a valid API key."}})

    with mock_vendor_http(bad_key), pytest.raises(InvalidCredentialError):
        await GeminiAdapter(ProviderCredentials("k")).test(None)


async def test_openai_retries_without_temperature_for_reasoning_models():
    payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        payloads.append(body)
        if "temperature" in body:
            return httpx.Response(
                400, json={"error": {"message": "Unsupported value: 'temperature' does not support 0.3"}}
            )
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    with mock_vendor_http(handler):
        result = await OpenAiAdapter(ProviderCredentials("k")).chat(
            "s", "u", model="o3-mini", temperature=0.3, max_tokens=10, timeout=5
        )
    assert result.text == "ok"
    assert len(payloads) == 2 and "temperature" not in payloads[1]


def test_registry_covers_all_providers():
    # The original four keep their resolution order; new vendors are appended.
    assert AI_PROVIDERS[:4] == ("openai", "anthropic", "gemini", "sarvam")
    assert set(AI_PROVIDERS[4:]) == {"mistral", "groq", "xai", "deepseek", "together", "openrouter", "perplexity"}
    for provider in AI_PROVIDERS:
        assert get_adapter(provider, ProviderCredentials("k")).label
    with pytest.raises(ValueError):
        get_adapter("nope", ProviderCredentials("k"))


# ---------------------------------------------------------------------------
# Provider endpoints (Integrations → AI)
# ---------------------------------------------------------------------------


async def test_provider_config_endpoints_mask_refresh_and_validate(client, vendors):
    headers = await _auth(client, "aiprov@example.com")

    initial = await client.get(f"{API}/integrations/ai/openai/config", headers=headers)
    assert initial.status_code == 200 and initial.json()["configured"] is False

    saved = await client.put(
        f"{API}/integrations/ai/openai/config",
        headers=headers,
        json={"api_key": "sk-openai-secret-4321", "default_model": "gpt-4o-mini"},
    )
    assert saved.status_code == 200, saved.text
    body = saved.json()
    assert "sk-openai-secret" not in saved.text
    assert body["api_key_masked"] == "****4321" and body["enabled"] is True
    assert body["model_count"] == 3 and body["default_model"] == "gpt-4o-mini"
    assert body["last_test_ok"] is True and body["models_refresh_error"] is None

    models = (await client.get(f"{API}/integrations/ai/openai/models", headers=headers)).json()
    assert {m["model_id"] for m in models["models"]} == {"gpt-4o-mini", "o3-mini", "text-embedding-3-small"}

    # Not in the cached catalog -> rejected unless flagged custom.
    bad = await client.put(
        f"{API}/integrations/ai/openai/config", headers=headers, json={"default_model": "gpt-9-preview"}
    )
    assert bad.status_code == 400
    custom = await client.put(
        f"{API}/integrations/ai/openai/config",
        headers=headers,
        json={"default_model": "gpt-9-preview", "custom_model": True},
    )
    assert custom.status_code == 200 and custom.json()["default_model"] == "gpt-9-preview"
    assert custom.json()["api_key_masked"] == "****4321"  # blank key kept

    # Embedding models are not valid chat defaults.
    embed = await client.put(
        f"{API}/integrations/ai/openai/config", headers=headers, json={"default_model": "text-embedding-3-small"}
    )
    assert embed.status_code == 400

    listing = (await client.get(f"{API}/integrations", headers=headers)).json()
    rows = listing["items"] if isinstance(listing, dict) else listing
    assert all(r["config_json"] is None for r in rows if r["provider"] == "openai")


async def test_provider_endpoint_validation(client, vendors):
    headers = await _auth(client, "aivalid@example.com")
    assert (await client.get(f"{API}/integrations/ai/nope/config", headers=headers)).status_code == 404
    assert (await client.post(f"{API}/integrations/ai/github/test", headers=headers)).status_code == 404
    http_url = await client.put(
        f"{API}/integrations/ai/openai/config", headers=headers, json={"base_url": "http://insecure.example.com"}
    )
    assert http_url.status_code == 422
    anthropic_url = await client.put(
        f"{API}/integrations/ai/anthropic/config", headers=headers, json={"base_url": "https://proxy.example.com"}
    )
    assert anthropic_url.status_code == 400
    bad_model = await client.put(
        f"{API}/integrations/ai/openai/config", headers=headers, json={"default_model": "has spaces"}
    )
    assert bad_model.status_code == 422
    refresh = await client.post(f"{API}/integrations/ai/gemini/models/refresh", headers=headers)
    assert refresh.status_code == 400 and refresh.json()["detail"]["code"] == "missing_credential"


async def test_provider_test_and_refresh_error_mapping(client, vendors):
    headers = await _auth(client, "aitest@example.com")
    await _connect(client, headers, "anthropic", "sk-ant-9999")

    ok = await client.post(f"{API}/integrations/ai/anthropic/test", headers=headers)
    assert ok.status_code == 200 and ok.json()["ok"] is True

    vendors.status["api.anthropic.com"] = 401
    failed = await client.post(f"{API}/integrations/ai/anthropic/test", headers=headers)
    assert failed.json()["ok"] is False and "sk-ant" not in failed.text
    status = (await client.get(f"{API}/integrations/ai/anthropic/config", headers=headers)).json()
    assert status["last_test_ok"] is False

    refresh = await client.post(f"{API}/integrations/ai/anthropic/models/refresh", headers=headers)
    assert refresh.status_code == 401 and refresh.json()["detail"]["code"] == "invalid_credential"


async def test_save_reports_refresh_failure_without_failing(client, vendors):
    headers = await _auth(client, "airefreshfail@example.com")
    vendors.status["generativelanguage.googleapis.com"] = 503
    body = await _connect(client, headers, "gemini", "g-key-0000")
    assert body["configured"] is True and body["status"] == "error"
    assert body["models_refresh_error"]


# ---------------------------------------------------------------------------
# Use cases + settings
# ---------------------------------------------------------------------------


async def test_use_case_options_come_from_cached_catalogs(client, vendors):
    headers = await _auth(client, "aiusecases@example.com")
    await _connect(client, headers, "openai", "sk-o-1111")
    await _connect(client, headers, "anthropic", "sk-a-2222")

    cases = {c["use_case"]: c for c in (await client.get(f"{API}/ai/use-cases", headers=headers)).json()}
    assert set(cases) == {
        "communication.writing_feedback",
        "ai.rag_chat",
        "coaches.chat",
        "reports.ai_briefing",
        "analytics.insights",
    }
    options = {(o["provider"], o["model"]) for o in cases["ai.rag_chat"]["options"]}
    assert ("anthropic", "claude-opus-5-5") in options and ("openai", "gpt-4o-mini") in options
    assert ("openai", "text-embedding-3-small") not in options  # capability filter

    rejected = await client.put(
        f"{API}/ai/use-cases/ai.rag_chat/model", headers=headers, json={"provider": "openai", "model": "gpt-x"}
    )
    assert rejected.status_code == 400
    custom = await client.put(
        f"{API}/ai/use-cases/ai.rag_chat/model",
        headers=headers,
        json={"provider": "openai", "model": "gpt-x", "custom": True},
    )
    assert custom.status_code == 200 and custom.json()["current"]["model"] == "gpt-x"
    not_connected = await client.put(
        f"{API}/ai/use-cases/ai.rag_chat/model",
        headers=headers,
        json={"provider": "gemini", "model": "gemini-2.5-flash", "custom": True},
    )
    assert not_connected.status_code == 400
    unknown = await client.put(
        f"{API}/ai/use-cases/nope.case/model", headers=headers, json={"provider": "openai", "model": "gpt-4o-mini"}
    )
    assert unknown.status_code == 404


async def test_clearing_a_use_case_returns_to_automatic(client, vendors):
    headers = await _auth(client, "aiclear@example.com")
    await _connect(client, headers, "openai", "sk-clr-1", default_model="gpt-4o-mini")
    url = f"{API}/ai/use-cases/coaches.chat/model"
    await client.put(url, headers=headers, json={"provider": "openai", "model": "o3-mini"})

    cleared = await client.delete(url, headers=headers)
    assert cleared.status_code == 200
    current = cleared.json()["current"]
    assert current["model"] == "gpt-4o-mini" and current["updated_at"] is None  # automatic

    history = (await client.get(f"{API}/ai/use-cases/coaches.chat/history", headers=headers)).json()
    assert history[0]["model"] == "o3-mini" and history[0]["effective_to"] is not None
    assert (await client.delete(f"{API}/ai/use-cases/nope.case/model", headers=headers)).status_code == 404


async def test_ai_settings_defaults_and_bounds(client):
    headers = await _auth(client, "aisettings@example.com")
    defaults = (await client.get(f"{API}/ai/settings", headers=headers)).json()
    assert defaults == {"default_provider": None, "timeout_seconds": 120, "max_tokens": 1200, "temperature": 0.3}

    too_short = await client.put(f"{API}/ai/settings", headers=headers, json={"timeout_seconds": 5})
    assert too_short.status_code == 422
    unknown = await client.put(f"{API}/ai/settings", headers=headers, json={"default_provider": "nope"})
    assert unknown.status_code == 400
    saved = await client.put(
        f"{API}/ai/settings", headers=headers, json={"default_provider": "anthropic", "max_tokens": 900}
    )
    assert saved.status_code == 200 and saved.json()["max_tokens"] == 900


# ---------------------------------------------------------------------------
# Gateway resolution order + BYOK > env
# ---------------------------------------------------------------------------


async def test_gateway_resolution_order(client, vendors):
    headers = await _auth(client, "aigateway@example.com")
    user_id = await _user_id(client, headers)

    async with client.session_factory() as session:
        with pytest.raises(MissingCredentialError):
            await AiGateway(session).resolve(user_id, USE_CASE_RAG_CHAT)

    # Env fallback (OpenAI only) when nothing is connected.
    env = get_settings().model_copy(update={"openai_api_key": "sk-env-key", "ai_chat_model": "gpt-env"})
    async with client.session_factory() as session:
        resolved = await AiGateway(session, env).resolve(user_id, USE_CASE_RAG_CHAT)
        assert (resolved.provider, resolved.model) == ("openai", "gpt-env")
        assert (await AiGateway(session, env).credentials(user_id, "openai")).api_key == "sk-env-key"

    # BYOK beats env; first connected provider in registry order wins.
    await _connect(client, headers, "anthropic", "sk-a-1", default_model="claude-opus-5-5")
    await _connect(client, headers, "openai", "sk-byok-1", default_model="gpt-4o-mini")
    async with client.session_factory() as session:
        gateway = AiGateway(session, env)
        assert (await gateway.credentials(user_id, "openai")).api_key == "sk-byok-1"
        resolved = await gateway.resolve(user_id, USE_CASE_RAG_CHAT)
        assert (resolved.provider, resolved.model) == ("openai", "gpt-4o-mini")

    # Default provider setting reorders; explicit selection beats everything.
    await client.put(f"{API}/ai/settings", headers=headers, json={"default_provider": "anthropic"})
    async with client.session_factory() as session:
        resolved = await AiGateway(session).resolve(user_id, USE_CASE_RAG_CHAT)
        assert resolved.provider == "anthropic" and resolved.model == "claude-opus-5-5"
    await client.put(
        f"{API}/ai/use-cases/ai.rag_chat/model", headers=headers, json={"provider": "openai", "model": "o3-mini"}
    )
    async with client.session_factory() as session:
        resolved = await AiGateway(session).resolve(user_id, USE_CASE_RAG_CHAT)
        assert (resolved.provider, resolved.model) == ("openai", "o3-mini")

    # A selected provider that gets disabled fails clearly instead of silently switching.
    conn_id = (await client.get(f"{API}/integrations/ai/openai/config", headers=headers)).json()["connection_id"]
    await client.patch(f"{API}/integrations/{conn_id}", headers=headers, json={"enabled": False})
    async with client.session_factory() as session:
        with pytest.raises(MissingCredentialError, match="OpenAI"):
            await AiGateway(session).resolve(user_id, USE_CASE_RAG_CHAT)


async def test_legacy_sarvam_user_keeps_default_model(client, vendors):
    headers = await _auth(client, "ailegacy@example.com")
    user_id = await _user_id(client, headers)
    await _connect(client, headers, "sarvam", "sarvam-key-1")
    async with client.session_factory() as session:
        resolved = await AiGateway(session).resolve(user_id, USE_CASE_WRITING_FEEDBACK)
    assert (resolved.provider, resolved.model) == ("sarvam", "sarvam-105b")


# ---------------------------------------------------------------------------
# Call sites: writing, RAG chat, coaches, reports, analytics insights
# ---------------------------------------------------------------------------


async def _writing(client, headers) -> str:
    created = await client.post(
        f"{API}/communication/writing",
        headers=headers,
        json={"title": "Draft", "content": "He go to school yesterday.", "category": "notes"},
    )
    assert created.status_code == 201
    return created.json()["id"]


async def test_writing_feedback_with_openai(client, vendors):
    headers = await _auth(client, "aiwriteopenai@example.com")
    await _connect(client, headers, "openai", "sk-w-1", default_model="gpt-4o-mini")
    writing_id = await _writing(client, headers)
    vendors.chat_text = f"```json\n{EVALUATION_JSON}\n```"

    res = await client.post(f"{API}/communication/writing/{writing_id}/ai-feedback", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["provider"] == "openai" and body["model"] == "gpt-4o-mini"
    assert body["overall_score"] == 80
    assert vendors.bodies("api.openai.com")[-1]["model"] == "gpt-4o-mini"


async def test_writing_rewrite_with_anthropic_selection(client, vendors):
    headers = await _auth(client, "aiwriteanthropic@example.com")
    await _connect(client, headers, "openai", "sk-w-2")
    await _connect(client, headers, "anthropic", "sk-w-3")
    await client.put(
        f"{API}/ai/use-cases/communication.writing_feedback/model",
        headers=headers,
        json={"provider": "anthropic", "model": "claude-opus-5-5"},
    )
    writing_id = await _writing(client, headers)
    vendors.chat_text = REWRITE_JSON

    res = await client.post(f"{API}/communication/writing/{writing_id}/ai-rewrite", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["suggested_text"] == "He went to school yesterday."
    assert vendors.bodies("api.anthropic.com")[-1]["model"] == "claude-opus-5-5"


async def test_writing_errors_map_to_codes(client, vendors):
    headers = await _auth(client, "aiwriteerr@example.com")
    writing_id = await _writing(client, headers)
    missing = await client.post(f"{API}/communication/writing/{writing_id}/ai-feedback", headers=headers)
    assert missing.status_code == 400 and missing.json()["detail"]["code"] == "missing_credential"

    await _connect(client, headers, "gemini", "g-w-1", default_model="gemini-2.5-flash")
    vendors.chat_text = "not json"
    malformed = await client.post(f"{API}/communication/writing/{writing_id}/ai-feedback", headers=headers)
    assert malformed.status_code == 502 and malformed.json()["detail"]["code"] == "malformed_response"


async def test_rag_chat_coaches_and_reports_use_gateway(client, vendors):
    headers = await _auth(client, "aicallsites@example.com")
    await _connect(client, headers, "anthropic", "sk-cs-1", default_model="claude-opus-5-5")
    vendors.chat_text = "Gateway says hi"

    chat = await client.post(f"{API}/ai/chat", headers=headers, json={"message": "What are my goals?"})
    assert chat.json()["reply"] == "Gateway says hi"
    status = (await client.get(f"{API}/ai/status", headers=headers)).json()
    assert status == {**status, "enabled": True, "provider": "anthropic"}

    coach = await client.post(f"{API}/coaches/habits/chat", headers=headers, json={"message": "Help"})
    assert coach.status_code == 200 and coach.json()["reply"] == "Gateway says hi"

    review = await client.post(f"{API}/reports/reviews/daily", headers=headers)
    assert review.status_code == 200 and review.json()["content"] == "Gateway says hi"
    # No embeddings without an OpenAI key, and no call ever reached another vendor.
    assert {r.url.host for r in vendors.requests} == {"api.anthropic.com"}


async def test_offline_messages_without_provider(client):
    headers = await _auth(client, "aioffline@example.com")
    coach = await client.post(f"{API}/coaches/habits/chat", headers=headers, json={"message": "Help"})
    assert "Integrations → AI" in coach.json()["reply"]
    chat = await client.post(f"{API}/ai/chat", headers=headers, json={"message": "Anything"})
    assert "Integrations → AI" in chat.json()["reply"]


async def test_analytics_insights_placeholder_then_llm(client, vendors):
    analytics_cache.clear()
    headers = await _auth(client, "aiinsights@example.com")
    placeholder = (await client.get(f"{API}/analytics/dashboard/ai", headers=headers)).json()
    assert placeholder["daily"]["status"] == "coming_soon"

    await _connect(client, headers, "openai", "sk-ins-1", default_model="gpt-4o-mini")
    vendors.chat_text = json.dumps(
        {"daily": ["Finish one task"], "weekly": ["Good streak"], "monthly": [], "predictions": ["On track"]}
    )
    analytics_cache.clear()
    ready = (await client.get(f"{API}/analytics/dashboard/ai", headers=headers)).json()
    assert ready["daily"] == {**ready["daily"], "status": "ready", "items": ["Finish one task"]}
    assert ready["monthly"]["items"] == [] and ready["monthly"]["message"]
    analytics_cache.clear()


# ---------------------------------------------------------------------------
# More providers, manual model ids, per-model test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "provider,expected",
    [
        ("groq", {"llama-3.3-70b-versatile": {CAPABILITY_CHAT}}),
        ("xai", {"grok-4": {CAPABILITY_CHAT}}),
        ("deepseek", {"deepseek-chat": {CAPABILITY_CHAT}, "deepseek-reasoner": {CAPABILITY_CHAT}}),
        ("mistral", {"mistral-large-latest": {CAPABILITY_CHAT, "vision"}, "mistral-embed": {CAPABILITY_EMBEDDING}}),
        (
            "together",
            {
                "meta-llama/Llama-3.3-70B-Instruct-Turbo": {CAPABILITY_CHAT},
                "BAAI/bge-large-en-v1.5": {CAPABILITY_EMBEDDING},
            },
        ),
        ("openrouter", {"anthropic/claude-opus-5": {CAPABILITY_CHAT, "vision"}}),
    ],
)
async def test_compatible_vendor_model_lists(vendors, provider, expected):
    adapter = get_adapter(provider, ProviderCredentials("k"))
    models = {m.model_id: m.capabilities for m in await adapter.list_models()}
    assert models == expected
    assert vendors.requests[-1].headers["Authorization"] == "Bearer k"


async def test_compatible_vendor_chat_uses_its_base_url(vendors):
    result = await get_adapter("groq", ProviderCredentials("k")).chat(
        "s", "u", model="llama-3.3-70b-versatile", temperature=0.2, max_tokens=10, timeout=5
    )
    assert result.text == "Mocked reply"
    req = vendors.requests[-1]
    assert str(req.url) == "https://api.groq.com/openai/v1/chat/completions"
    assert json.loads(req.content)["max_tokens"] == 10


async def test_manual_model_ids_survive_refresh(client, vendors):
    headers = await _auth(client, "aimanual@example.com")
    await _connect(client, headers, "openrouter", "or-key-1")
    url = f"{API}/integrations/ai/openrouter/models"

    added = await client.post(url, headers=headers, json={"model_id": "meta-llama/llama-4-maverick:free"})
    assert added.status_code == 200
    duplicate = await client.post(url, headers=headers, json={"model_id": "meta-llama/llama-4-maverick:free"})
    assert duplicate.status_code == 409

    refreshed = await client.post(f"{url}/refresh", headers=headers)
    sources = {m["model_id"]: m["source"] for m in refreshed.json()["models"]}
    assert sources == {"anthropic/claude-opus-5": "fetched", "meta-llama/llama-4-maverick:free": "manual"}

    # Added ids appear in use-case options and can be a default model without the custom flag.
    cases = {c["use_case"]: c for c in (await client.get(f"{API}/ai/use-cases", headers=headers)).json()}
    assert ("openrouter", "meta-llama/llama-4-maverick:free") in {
        (o["provider"], o["model"]) for o in cases["coaches.chat"]["options"]
    }
    default = await client.put(
        f"{API}/integrations/ai/openrouter/config",
        headers=headers,
        json={"default_model": "meta-llama/llama-4-maverick:free"},
    )
    assert default.status_code == 200

    fetched = await client.post(f"{url}/remove", headers=headers, json={"model_id": "anthropic/claude-opus-5"})
    assert fetched.status_code == 400
    missing = await client.post(f"{url}/remove", headers=headers, json={"model_id": "nope/model"})
    assert missing.status_code == 404
    removed = await client.post(f"{url}/remove", headers=headers, json={"model_id": "meta-llama/llama-4-maverick:free"})
    assert [m["model_id"] for m in removed.json()["models"]] == ["anthropic/claude-opus-5"]


async def test_per_model_test(client, vendors):
    headers = await _auth(client, "aimodeltest@example.com")
    await _connect(client, headers, "deepseek", "ds-key-1")
    url = f"{API}/integrations/ai/deepseek/models/test"

    ok = await client.post(url, headers=headers, json={"model_id": "deepseek-chat"})
    assert ok.json() == {"ok": True, "detail": "Model responded", "model_id": "deepseek-chat"}
    assert json.loads(vendors.requests[-1].content)["model"] == "deepseek-chat"

    vendors.chat_text = "   "  # reasoning model used its tiny budget: reachable, not a failure
    empty = await client.post(url, headers=headers, json={"model_id": "deepseek-reasoner"})
    assert empty.json()["ok"] is True and "Reachable" in empty.json()["detail"]

    vendors.status["api.deepseek.com"] = 404
    failed = await client.post(url, headers=headers, json={"model_id": "deepseek-v9"})
    assert failed.json()["ok"] is False and "HTTP 404" in failed.json()["detail"]
    assert "ds-key-1" not in failed.text


async def test_providers_without_listing_seed_suggestions_without_network(client, vendors):
    headers = await _auth(client, "ainolisting@example.com")
    body = await _connect(client, headers, "perplexity", "pplx-key-1")
    assert body["supports_model_listing"] is False and body["status"] == "connected"
    assert not vendors.requests  # saving a key makes no vendor call for no-listing providers

    models = (await client.get(f"{API}/integrations/ai/perplexity/models", headers=headers)).json()["models"]
    assert [m["model_id"] for m in models] == ["sonar", "sonar-deep-research", "sonar-pro", "sonar-reasoning-pro"]
    assert {m["source"] for m in models} == {"manual"}

    refresh = await client.post(f"{API}/integrations/ai/perplexity/models/refresh", headers=headers)
    assert refresh.status_code == 400

    sarvam = await _connect(client, headers, "sarvam", "sarvam-key-2")
    assert sarvam["model_count"] == 2

    test = await client.post(f"{API}/integrations/ai/perplexity/test", headers=headers)
    assert test.json()["ok"] is True and test.json()["model"] == "sonar"
    assert str(vendors.requests[-1].url) == "https://api.perplexity.ai/chat/completions"


async def test_source_column_migration_backfills_existing_rows():
    from app.core.migrations import ensure_columns
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "CREATE TABLE ai_provider_models (id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36), "
                "provider VARCHAR(32), model_id VARCHAR(80), display_name VARCHAR(120), "
                "capabilities VARCHAR(64), refreshed_at DATETIME)"
            )
        )
        await conn.execute(text("INSERT INTO ai_provider_models (id, model_id) VALUES ('1', 'gpt-4o-mini')"))
        await ensure_columns(conn)
        row = (await conn.execute(text("SELECT source FROM ai_provider_models"))).one()
    await engine.dispose()
    assert row.source == "fetched"
