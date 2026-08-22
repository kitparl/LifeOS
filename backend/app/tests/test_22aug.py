import pytest


async def _auth_token(client, email):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),
            "email": email,
            "password": "password123",
            "display_name": "Aug22 User",
        },
    )
    return reg.json()["access_token"]


async def _subject_with_sections(client, headers, title_a="Alpha", title_b="Beta"):
    subject = await client.post(
        "/api/v1/knowledge-notes/subjects",
        headers=headers,
        json={"title": "KN Aug22"},
    )
    subject_id = subject.json()["id"]
    chapter_a = await client.post(
        f"/api/v1/knowledge-notes/subjects/{subject_id}/chapters",
        headers=headers,
        json={"title": "Chapter A"},
    )
    chapter_b = await client.post(
        f"/api/v1/knowledge-notes/subjects/{subject_id}/chapters",
        headers=headers,
        json={"title": "Chapter B"},
    )
    section_a = await client.post(
        f"/api/v1/knowledge-notes/chapters/{chapter_a.json()['id']}/sections",
        headers=headers,
        json={"title": title_a, "content": "machine learning basics"},
    )
    section_b = await client.post(
        f"/api/v1/knowledge-notes/chapters/{chapter_b.json()['id']}/sections",
        headers=headers,
        json={"title": title_b, "content": "neural networks overview"},
    )
    return subject_id, section_a.json()["id"], section_b.json()["id"], chapter_a.json()["id"]


@pytest.mark.asyncio
async def test_search_filters_by_subject_id(client):
    token = await _auth_token(client, "kn22-search@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    subject_a, section_a, _, _ = await _subject_with_sections(client, headers, "ML Basics", "Other")
    subject_b = await client.post(
        "/api/v1/knowledge-notes/subjects",
        headers=headers,
        json={"title": "Other Subject"},
    )
    chapter_b = await client.post(
        f"/api/v1/knowledge-notes/subjects/{subject_b.json()['id']}/chapters",
        headers=headers,
        json={"title": "Only"},
    )
    await client.post(
        f"/api/v1/knowledge-notes/chapters/{chapter_b.json()['id']}/sections",
        headers=headers,
        json={"title": "Noise", "content": "machine learning elsewhere"},
    )

    scoped = await client.get(
        "/api/v1/knowledge-notes/search",
        headers=headers,
        params={"q": "machine learning", "subject_id": subject_a},
    )
    assert scoped.status_code == 200
    hits = scoped.json()
    assert len(hits) == 1
    assert hits[0]["section_id"] == section_a
    assert hits[0]["subject_id"] == subject_a

    global_hits = await client.get(
        "/api/v1/knowledge-notes/search",
        headers=headers,
        params={"q": "machine learning"},
    )
    assert len(global_hits.json()) >= 2


@pytest.mark.asyncio
async def test_section_closed_flag_persists(client):
    token = await _auth_token(client, "kn22-close-sec@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, section_id, _, _ = await _subject_with_sections(client, headers)

    closed = await client.patch(
        f"/api/v1/knowledge-notes/sections/{section_id}",
        headers=headers,
        json={"closed": True},
    )
    assert closed.status_code == 200
    assert closed.json()["closed_at"] is not None

    detail = await client.get(
        f"/api/v1/knowledge-notes/sections/{section_id}",
        headers=headers,
    )
    assert detail.json()["closed_at"] is not None

    reopened = await client.patch(
        f"/api/v1/knowledge-notes/sections/{section_id}",
        headers=headers,
        json={"closed": False},
    )
    assert reopened.status_code == 200
    assert reopened.json()["closed_at"] is None


@pytest.mark.asyncio
async def test_chapter_closed_flag_persists(client):
    token = await _auth_token(client, "kn22-close-ch@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    subject_id, _, _, chapter_id = await _subject_with_sections(client, headers)

    closed = await client.patch(
        f"/api/v1/knowledge-notes/chapters/{chapter_id}",
        headers=headers,
        json={"closed": True},
    )
    assert closed.status_code == 200
    assert closed.json()["closed_at"] is not None

    detail = await client.get(f"/api/v1/knowledge-notes/subjects/{subject_id}", headers=headers)
    chapter = detail.json()["chapters"][0]
    assert chapter["closed_at"] is not None

    reopened = await client.patch(
        f"/api/v1/knowledge-notes/chapters/{chapter_id}",
        headers=headers,
        json={"closed": False},
    )
    assert reopened.json()["closed_at"] is None
