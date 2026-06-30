import pytest


async def _auth(client, email="phase3@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Phase3"},
    )
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.mark.asyncio
async def test_memory_crud(client):
    h = await _auth(client)
    created = await client.post(
        "/api/v1/memory/items",
        headers=h,
        json={"memory_key": "wake_time", "memory_value": "6:00 AM", "category": "preference"},
    )
    assert created.status_code == 201
    summary = await client.get("/api/v1/memory/summary", headers=h)
    assert summary.json()["total"] == 1


@pytest.mark.asyncio
async def test_coaches_chat(client):
    h = await _auth(client, "p3coach@example.com")
    res = await client.post(
        "/api/v1/coaches/running/chat",
        headers=h,
        json={"message": "How is my training?"},
    )
    assert res.status_code == 200
    assert "reply" in res.json()


@pytest.mark.asyncio
async def test_ocr_voice_integrations(client):
    h = await _auth(client, "p3ovi@example.com")
    ocr = await client.post(
        "/api/v1/ocr/documents",
        headers=h,
        json={"filename": "receipt.txt", "doc_type": "receipt", "text": "Total: $12.50"},
    )
    assert ocr.status_code == 201
    voice = await client.post(
        "/api/v1/voice/command",
        headers=h,
        json={"transcript": "go to tasks"},
    )
    assert voice.status_code == 200
    assert voice.json()["route"] == "/tasks"
    providers = await client.get("/api/v1/integrations/providers", headers=h)
    assert len(providers.json()) >= 5
    conn = await client.post("/api/v1/integrations", headers=h, json={"provider": "telegram", "enabled": True})
    assert conn.status_code == 201


@pytest.mark.asyncio
async def test_automations_predictions_life_timeline(client):
    h = await _auth(client, "p3apl@example.com")
    rule = await client.post(
        "/api/v1/automations/rules",
        headers=h,
        json={
            "name": "Journal reminder",
            "trigger_type": "no_journal_days",
            "action_type": "notify",
            "condition_json": '{"days": 3}',
        },
    )
    assert rule.status_code == 201
    eval_res = await client.post("/api/v1/automations/evaluate", headers=h)
    assert eval_res.status_code == 200
    preds = await client.get("/api/v1/predictions/summary", headers=h)
    assert preds.status_code == 200
    assert "running_readiness" in preds.json()
    milestone = await client.post(
        "/api/v1/life-timeline/milestones",
        headers=h,
        json={"title": "Started LifeOS", "milestone_date": "2026-01-01"},
    )
    assert milestone.status_code == 201
    timeline = await client.get("/api/v1/life-timeline", headers=h)
    assert timeline.status_code == 200
    assert len(timeline.json()) >= 1
