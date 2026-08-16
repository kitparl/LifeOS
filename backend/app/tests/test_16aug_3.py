import pytest


async def _auth_token(client, email):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),
            "email": email,
            "password": "password123",
            "display_name": "Aug3 User",
        },
    )
    return reg.json()["access_token"]


async def _section(client, headers, email_tag="kn"):
    subject = await client.post(
        "/api/v1/knowledge-notes/subjects",
        headers=headers,
        json={"title": f"Subject {email_tag}"},
    )
    assert subject.status_code == 201
    subject_id = subject.json()["id"]
    chapter = await client.post(
        f"/api/v1/knowledge-notes/subjects/{subject_id}/chapters",
        headers=headers,
        json={"title": "Chapter"},
    )
    chapter_id = chapter.json()["id"]
    section = await client.post(
        f"/api/v1/knowledge-notes/chapters/{chapter_id}/sections",
        headers=headers,
        json={"title": "Section", "content": "notes"},
    )
    return subject_id, chapter_id, section.json()["id"]


async def _upload(client, headers, section_id, name="note.txt", body=b"section-bytes"):
    return await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": (name, body, "text/plain")},
        data={"module": "knowledge_notes", "entity_id": section_id},
    )


@pytest.mark.asyncio
async def test_section_attachments_are_scoped(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))
    token = await _auth_token(client, "kn-attach@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, _, section_a = await _section(client, headers, "a")
    _, _, section_b = await _section(client, headers, "b")

    uploaded = await _upload(client, headers, section_a, "a.txt", b"only-a")
    assert uploaded.status_code == 201
    assert uploaded.json()["module"] == "knowledge_notes"
    assert uploaded.json()["entity_id"] == section_a

    listed_a = await client.get(
        "/api/v1/files",
        headers=headers,
        params={"module": "knowledge_notes", "entity_id": section_a},
    )
    listed_b = await client.get(
        "/api/v1/files",
        headers=headers,
        params={"module": "knowledge_notes", "entity_id": section_b},
    )
    assert len(listed_a.json()) == 1
    assert listed_a.json()[0]["filename"] == "a.txt"
    assert listed_b.json() == []


@pytest.mark.asyncio
async def test_archive_keeps_section_attachments(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))
    token = await _auth_token(client, "kn-keep@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    subject_id, _, section_id = await _section(client, headers, "keep")

    uploaded = await _upload(client, headers, section_id)
    assert uploaded.status_code == 201

    archived = await client.post(
        f"/api/v1/knowledge-notes/sections/{section_id}/archive",
        headers=headers,
    )
    assert archived.status_code == 200

    detail = await client.get(f"/api/v1/knowledge-notes/subjects/{subject_id}", headers=headers)
    assert any(sec["id"] == section_id for sec in detail.json()["archived_sections"])

    listed = await client.get(
        "/api/v1/files",
        headers=headers,
        params={"module": "knowledge_notes", "entity_id": section_id},
    )
    assert len(listed.json()) == 1


@pytest.mark.asyncio
async def test_permanent_section_delete_soft_deletes_files(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))
    token = await _auth_token(client, "kn-del@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, _, section_id = await _section(client, headers, "del")

    uploaded = await _upload(client, headers, section_id, "gone.txt", b"delete-me")
    file_id = uploaded.json()["id"]

    deleted = await client.delete(f"/api/v1/knowledge-notes/sections/{section_id}", headers=headers)
    assert deleted.status_code == 204

    listed = await client.get(
        "/api/v1/files",
        headers=headers,
        params={"module": "knowledge_notes", "entity_id": section_id},
    )
    assert listed.json() == []
    missing = await client.get(f"/api/v1/files/{file_id}", headers=headers)
    assert missing.status_code == 404

    usage = await client.get("/api/v1/files/usage", headers=headers)
    assert usage.status_code == 200
    assert usage.json()["file_count"] == 1


@pytest.mark.asyncio
async def test_expired_archive_purge_soft_deletes_files(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr("app.modules.knowledge_notes.service.ARCHIVE_TTL_DAYS", 0)
    token = await _auth_token(client, "kn-purge-files@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    subject_id, _, section_id = await _section(client, headers, "purge")

    uploaded = await _upload(client, headers, section_id, "old.txt", b"old-bytes")
    file_id = uploaded.json()["id"]
    await client.post(f"/api/v1/knowledge-notes/sections/{section_id}/archive", headers=headers)

    detail = await client.get(f"/api/v1/knowledge-notes/subjects/{subject_id}", headers=headers)
    assert detail.json()["archived_sections"] == []

    listed = await client.get(
        "/api/v1/files",
        headers=headers,
        params={"module": "knowledge_notes", "entity_id": section_id},
    )
    assert listed.json() == []
    missing = await client.get(f"/api/v1/files/{file_id}", headers=headers)
    assert missing.status_code == 404
    usage = await client.get("/api/v1/files/usage", headers=headers)
    assert usage.json()["file_count"] == 1
