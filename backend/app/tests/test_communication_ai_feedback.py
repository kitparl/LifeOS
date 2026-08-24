"""Tests for AI writing feedback, Sarvam BYOK, and use-case model selection."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.crypto import decrypt, encrypt
from app.modules.communication.ai.metrics import compute_deterministic_metrics
from app.modules.communication.ai.provider import (
    InvalidCredentialError,
    MalformedResponseError,
    _validate_canonical,
)
from app.modules.communication.ai.rubric import compute_overall_score, normalize_dimensions
from app.modules.integrations.sarvam_config import mask_config, parse_config, serialize_config


async def _auth(client, email="aiwrite@example.com"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": ("usr_" + email.split("@")[0].replace(".", "")[:26]),
            "email": email,
            "password": "password123",
            "display_name": "AI Write",
        },
    )
    assert reg.status_code in (200, 201), reg.text
    return reg.json()["access_token"]


def test_sarvam_encrypt_decrypt_roundtrip():
    raw = "test-sarvam-key-abcdef"
    serialized = serialize_config(api_key=raw)
    parsed = parse_config(serialized)
    assert parsed is not None
    assert parsed.api_key == raw
    masked = mask_config(serialized)
    assert masked.configured is True
    assert masked.api_key_masked is not None
    assert raw not in (masked.api_key_masked or "")
    assert "cdef" in (masked.api_key_masked or "")


def test_crypto_helpers():
    token = encrypt("secret-value")
    assert decrypt(token) == "secret-value"


def test_rubric_overall_is_app_computed():
    dims = normalize_dimensions({d: 80 for d in ("grammar", "clarity")})
    # missing dims become 0 — overall should not be LLM-invented
    score = compute_overall_score(dims)
    assert 0 <= score <= 100
    assert score < 80  # many zeros pull average down


def test_deterministic_metrics():
    m = compute_deterministic_metrics("Hello world. Another sentence!\n\nNew paragraph.")
    assert m["wordCount"] >= 4
    assert m["sentenceCount"] >= 2
    assert m["paragraphCount"] >= 2


def test_validate_canonical_rejects_trust_of_llm_overall():
    raw = {
        "dimensions": {k: 90 for k in (
            "grammar", "punctuation", "spelling", "clarity", "readability",
            "vocabulary", "sentenceVariety", "coherence", "structure",
            "conciseness", "tone", "intentAlignment", "audienceAppropriateness",
        )},
        "overallScore": 10,  # ignored
        "strengths": ["Clear"],
        "issues": [],
        "suggestions": [],
        "alreadyStrong": True,
    }
    out = _validate_canonical(raw, provider="sarvam", model="sarvam-105b")
    assert out["overallScore"] == 90
    assert out["alreadyStrong"] is True


@pytest.mark.asyncio
async def test_sarvam_status_and_save(client):
    token = await _auth(client, "sarvamcfg@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    status = await client.get("/api/v1/integrations/sarvam", headers=headers)
    assert status.status_code == 200
    assert status.json()["configured"] is False

    saved = await client.put(
        "/api/v1/integrations/sarvam/config",
        headers=headers,
        json={"api_key": "sk-test-sarvam-key-9999", "enabled": True},
    )
    assert saved.status_code == 200
    body = saved.json()
    assert body["configured"] is True
    assert body["api_key_masked"] is not None
    assert "sk-test" not in (body["api_key_masked"] or "")
    assert "9999" in (body["api_key_masked"] or "")


@pytest.mark.asyncio
async def test_use_case_model_selection_history(client):
    token = await _auth(client, "modelcfg@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Connect Sarvam so the model becomes selectable
    await client.put(
        "/api/v1/integrations/sarvam/config",
        headers=headers,
        json={"api_key": "sk-model-select-1111", "enabled": True},
    )

    listing = await client.get("/api/v1/ai/use-cases", headers=headers)
    assert listing.status_code == 200
    cases = listing.json()
    assert any(c["use_case"] == "communication.writing_feedback" for c in cases)

    put = await client.put(
        "/api/v1/ai/use-cases/communication.writing_feedback/model",
        headers=headers,
        json={"provider": "sarvam", "model": "sarvam-105b"},
    )
    assert put.status_code == 200
    assert put.json()["current"]["model"] == "sarvam-105b"

    history = await client.get(
        "/api/v1/ai/use-cases/communication.writing_feedback/history",
        headers=headers,
    )
    assert history.status_code == 200
    rows = history.json()
    assert len(rows) >= 1
    assert rows[0]["provider"] == "sarvam"
    assert rows[0]["effective_to"] is None


@pytest.mark.asyncio
async def test_writing_feedback_idempotency_and_missing_key(client):
    token = await _auth(client, "feedback@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/communication/writing",
        headers=headers,
        json={"title": "Draft", "content": "He go to school yesterday.", "category": "notes"},
    )
    assert created.status_code == 201
    writing_id = created.json()["id"]

    missing = await client.post(
        f"/api/v1/communication/writing/{writing_id}/ai-feedback",
        headers=headers,
    )
    assert missing.status_code == 400
    detail = missing.json()["detail"]
    assert isinstance(detail, dict)
    assert detail["code"] == "missing_credential"

    await client.put(
        "/api/v1/integrations/sarvam/config",
        headers=headers,
        json={"api_key": "sk-feedback-2222", "enabled": True},
    )

    fake_result = {
        "evaluationVersion": "v1",
        "rubricVersion": "writing-rubric-v1",
        "promptVersion": "writing-feedback-v1",
        "provider": "sarvam",
        "model": "sarvam-105b",
        "overallScore": 70,
        "dimensions": {k: 70 for k in (
            "grammar", "punctuation", "spelling", "clarity", "readability",
            "vocabulary", "sentenceVariety", "coherence", "structure",
            "conciseness", "tone", "intentAlignment", "audienceAppropriateness",
        )},
        "strengths": ["Clear intent"],
        "issues": [
            {
                "location": "sentence 1",
                "problem_type": "Grammar",
                "severity": "high",
                "original_text": "He go to school yesterday.",
                "explanation": "Past tense needed",
                "suggestion": "He went to school yesterday.",
            }
        ],
        "suggestions": ["Check verb tense"],
        "alreadyStrong": False,
        "_usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }

    with patch(
        "app.modules.communication.service.SarvamWritingProvider.evaluate_writing",
        new_callable=AsyncMock,
        return_value=dict(fake_result),
    ) as mock_eval:
        first = await client.post(
            f"/api/v1/communication/writing/{writing_id}/ai-feedback",
            headers=headers,
        )
        assert first.status_code == 200, first.text
        body1 = first.json()
        assert body1["cached"] is False
        assert body1["overall_score"] == 70
        assert mock_eval.await_count == 1

        second = await client.post(
            f"/api/v1/communication/writing/{writing_id}/ai-feedback",
            headers=headers,
        )
        assert second.status_code == 200
        body2 = second.json()
        assert body2["cached"] is True
        assert body2["id"] == body1["id"]
        assert mock_eval.await_count == 1  # no second network call


@pytest.mark.asyncio
async def test_invalid_credential_mapping(client):
    token = await _auth(client, "badkey@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = await client.post(
        "/api/v1/communication/writing",
        headers=headers,
        json={"title": "T", "content": "Some content here.", "category": "notes"},
    )
    writing_id = created.json()["id"]
    await client.put(
        "/api/v1/integrations/sarvam/config",
        headers=headers,
        json={"api_key": "sk-bad", "enabled": True},
    )

    with patch(
        "app.modules.communication.service.SarvamWritingProvider.evaluate_writing",
        new_callable=AsyncMock,
        side_effect=InvalidCredentialError("Invalid or revoked Sarvam API key."),
    ):
        res = await client.post(
            f"/api/v1/communication/writing/{writing_id}/ai-feedback",
            headers=headers,
        )
        assert res.status_code == 401
        assert res.json()["detail"]["code"] == "invalid_credential"


def test_malformed_response_helper():
    with pytest.raises(MalformedResponseError):
        from app.modules.communication.ai.provider import _parse_json_object

        _parse_json_object("not json at all")


@pytest.mark.asyncio
async def test_writing_rewrite_idempotency(client):
    token = await _auth(client, "rewrite@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/communication/writing",
        headers=headers,
        json={"title": "Draft", "content": "He go to school yesterday.", "category": "notes"},
    )
    writing_id = created.json()["id"]

    await client.put(
        "/api/v1/integrations/sarvam/config",
        headers=headers,
        json={"api_key": "sk-rewrite-3333", "enabled": True},
    )

    fake_rewrite = {
        "promptVersion": "writing-rewrite-v1",
        "provider": "sarvam",
        "model": "sarvam-105b",
        "suggestedVersion": "He went to school yesterday.",
        "whyBetter": ["Correct past tense"],
        "keyChanges": ["go → went"],
        "_usage": {"prompt_tokens": 80, "completion_tokens": 40},
    }

    with patch(
        "app.modules.communication.service.SarvamWritingProvider.suggest_rewrite",
        new_callable=AsyncMock,
        return_value=dict(fake_rewrite),
    ) as mock_rewrite:
        first = await client.post(
            f"/api/v1/communication/writing/{writing_id}/ai-rewrite",
            headers=headers,
        )
        assert first.status_code == 200, first.text
        body1 = first.json()
        assert body1["cached"] is False
        assert body1["suggested_text"] == "He went to school yesterday."
        assert mock_rewrite.await_count == 1

        second = await client.post(
            f"/api/v1/communication/writing/{writing_id}/ai-rewrite",
            headers=headers,
        )
        assert second.status_code == 200
        body2 = second.json()
        assert body2["cached"] is True
        assert body2["id"] == body1["id"]
        assert mock_rewrite.await_count == 1
