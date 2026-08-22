import pytest


async def _auth_token(client, email: str) -> str:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),
            "email": email,
            "password": "password123",
            "display_name": "QA Views User",
        },
    )
    return reg.json()["access_token"]


async def _create_entry(client, headers, **kwargs):
    payload = {
        "question": kwargs.get("question", "Test question?"),
        "answer": kwargs.get("answer", "Test answer"),
        "type": kwargs.get("type"),
        "tags": kwargs.get("tags", []),
        "is_deep_personal": kwargs.get("is_deep_personal", False),
    }
    return await client.post("/api/v1/qa/entries", headers=headers, json=payload)


@pytest.mark.asyncio
async def test_qa_pagination_and_total_count(client):
    token = await _auth_token(client, "qapage@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(5):
        await _create_entry(client, headers, question=f"Question {i}?", answer=f"Answer {i}")

    page1 = await client.get("/api/v1/qa/entries?limit=2&offset=0", headers=headers)
    assert page1.status_code == 200
    assert len(page1.json()) == 2
    assert page1.headers.get("X-Total-Count") == "5"

    page2 = await client.get("/api/v1/qa/entries?limit=2&offset=2", headers=headers)
    assert page2.status_code == 200
    assert len(page2.json()) == 2
    assert page2.headers.get("X-Total-Count") == "5"


@pytest.mark.asyncio
async def test_qa_deep_personal_filter(client):
    token = await _auth_token(client, "qadeep@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await _create_entry(client, headers, question="Why did she leave?", is_deep_personal=True)
    await _create_entry(client, headers, question="What is n in math?", is_deep_personal=False)

    all_entries = await client.get("/api/v1/qa/entries", headers=headers)
    assert len(all_entries.json()) == 2

    deep = await client.get("/api/v1/qa/entries?deep_personal=true", headers=headers)
    assert deep.status_code == 200
    assert len(deep.json()) == 1
    assert deep.json()[0]["question"] == "Why did she leave?"
    assert deep.json()[0]["is_deep_personal"] is True


@pytest.mark.asyncio
async def test_qa_tag_filter(client):
    token = await _auth_token(client, "qatag@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await _create_entry(client, headers, question="Q1?", tags=["relationship"])
    await _create_entry(client, headers, question="Q2?", tags=["math"])

    filtered = await client.get("/api/v1/qa/entries?tag=relationship", headers=headers)
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["question"] == "Q1?"


@pytest.mark.asyncio
async def test_qa_include_answer_false(client):
    token = await _auth_token(client, "qanoans@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await _create_entry(client, headers, question="Secret?", answer="Hidden answer body")

    resp = await client.get("/api/v1/qa/entries?include_answer=false", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["current_answer"] is None


@pytest.mark.asyncio
async def test_qa_sort_by_created_at(client):
    token = await _auth_token(client, "qasort@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await _create_entry(client, headers, question="First?")
    await _create_entry(client, headers, question="Second?")

    resp = await client.get("/api/v1/qa/entries?sort_by=created_at", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    assert items[0]["created_at"] >= items[1]["created_at"]


@pytest.mark.asyncio
async def test_qa_create_update_is_deep_personal(client):
    token = await _auth_token(client, "qadeep2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = await _create_entry(client, headers, question="Should I go?", is_deep_personal=False)
    assert created.status_code == 201
    entry_id = created.json()["id"]
    assert created.json()["is_deep_personal"] is False

    updated = await client.patch(
        f"/api/v1/qa/entries/{entry_id}",
        headers=headers,
        json={"is_deep_personal": True},
    )
    assert updated.status_code == 200
    assert updated.json()["is_deep_personal"] is True

    listed = await client.get("/api/v1/qa/entries?deep_personal=true", headers=headers)
    assert len(listed.json()) == 1
