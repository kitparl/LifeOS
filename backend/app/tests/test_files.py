import pytest
from datetime import datetime, timedelta, timezone


async def _auth_token(client, email="files@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={
        "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),"email": email, "password": "password123", "display_name": "Files User"},
    )
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_file_upload_list_delete(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    token = await _auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("test.txt", b"hello lifeos", "text/plain")},
        data={"module": "wishlist"},
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["filename"] == "test.txt"
    assert body["storage_backend"] == "local"
    assert body["module"] == "wishlist"

    listed = await client.get("/api/v1/files", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    content = await client.get(f"/api/v1/files/{body['id']}/content", headers=headers)
    assert content.status_code == 200
    assert content.content == b"hello lifeos"

    deleted = await client.delete(f"/api/v1/files/{body['id']}", headers=headers)
    assert deleted.status_code == 204

    listed_after = await client.get("/api/v1/files", headers=headers)
    assert listed_after.json() == []


@pytest.mark.asyncio
async def test_duplicate_upload_rejected(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    token = await _auth_token(client, "dedupe@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"file": ("same.txt", b"identical-bytes", "text/plain")}
    data = {"module": "tasks", "entity_id": "task-1"}

    first = await client.post("/api/v1/files/upload", headers=headers, files=payload, data=data)
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("same-copy.txt", b"identical-bytes", "text/plain")},
        data=data,
    )
    assert second.status_code == 409
    assert "already been uploaded" in second.json()["detail"].lower()

    # Different entity may upload the same bytes
    other = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("same.txt", b"identical-bytes", "text/plain")},
        data={"module": "tasks", "entity_id": "task-2"},
    )
    assert other.status_code == 201


@pytest.mark.asyncio
async def test_file_upload_too_large(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "max_upload_bytes", 10)

    token = await _auth_token(client, "large@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("big.bin", b"x" * 100, "application/octet-stream")},
    )
    assert res.status_code == 413


@pytest.mark.asyncio
async def test_path_traversal_rejected(client, tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.modules.files.backends.local import LocalStorageBackend
    from fastapi import HTTPException

    settings = get_settings()
    root = tmp_path / "uploads"
    monkeypatch.setattr(settings, "upload_dir", str(root))

    backend = LocalStorageBackend(root)
    with pytest.raises(HTTPException) as exc:
        backend._resolve("../../etc/passwd")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_type_sniff_rejection(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    token = await _auth_token(client, "sniff@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # HTML disguised as .txt — extension vs content, or HTML extension rejected
    res = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("page.html", b"<!DOCTYPE html><html></html>", "text/html")},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_oversized_stream_abort(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "max_upload_bytes", 50)

    token = await _auth_token(client, "stream@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("note.txt", b"a" * 200, "text/plain")},
    )
    assert res.status_code == 413
    # No orphaned files under upload root for this key layout
    uploads = tmp_path / "uploads"
    if uploads.exists():
        leftovers = [p for p in uploads.rglob("*") if p.is_file() and not p.name.startswith(".tmp_")]
        assert leftovers == []


@pytest.mark.asyncio
async def test_quota_413(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "user_storage_quota_bytes", 20)

    token = await _auth_token(client, "quota@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("a.txt", b"hello world!!", "text/plain")},
        data={"module": "tasks"},
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("b.txt", b"another file here", "text/plain")},
        data={"module": "tasks"},
    )
    assert second.status_code == 413
    assert "quota" in second.json()["detail"].lower()


@pytest.mark.asyncio
async def test_rate_limit_429(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "uploads_per_hour", 1)

    token = await _auth_token(client, "rate@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("a.txt", b"one", "text/plain")},
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("b.txt", b"two", "text/plain")},
    )
    assert second.status_code == 429


@pytest.mark.asyncio
async def test_range_request(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    token = await _auth_token(client, "range@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("range.txt", b"0123456789", "text/plain")},
    )
    file_id = upload.json()["id"]

    res = await client.get(
        f"/api/v1/files/{file_id}/content",
        headers={**headers, "Range": "bytes=2-5"},
    )
    assert res.status_code == 206
    assert res.content == b"2345"
    assert res.headers["Content-Range"] == "bytes 2-5/10"


@pytest.mark.asyncio
async def test_token_download(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    token = await _auth_token(client, "tokendown@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("tok.txt", b"secret", "text/plain")},
    )
    file_id = upload.json()["id"]

    minted = await client.post(f"/api/v1/files/{file_id}/download-token", headers=headers)
    assert minted.status_code == 200
    dl_token = minted.json()["token"]

    # No Bearer — token query only
    content = await client.get(f"/api/v1/files/{file_id}/content?token={dl_token}")
    assert content.status_code == 200
    assert content.content == b"secret"


@pytest.mark.asyncio
async def test_content_headers_allow_unicode_filename(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    token = await _auth_token(client, "unicodefile@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    name = "Screenshot 16 at 9.51.00\u202fPM.txt"

    upload = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": (name, b"preview-bytes", "text/plain")},
    )
    assert upload.status_code == 201
    file_id = upload.json()["id"]

    minted = await client.post(f"/api/v1/files/{file_id}/download-token", headers=headers)
    content = await client.get(f"/api/v1/files/{file_id}/content?token={minted.json()['token']}")
    assert content.status_code == 200
    assert content.content == b"preview-bytes"
    disposition = content.headers["content-disposition"]
    disposition.encode("latin-1")
    assert "filename*=UTF-8''" in disposition
    assert "\u202f" not in disposition


@pytest.mark.asyncio
async def test_soft_delete_then_purge(client, tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.modules.auth.models import User
    from sqlalchemy import select

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "file_purge_after_days", 0)

    token = await _auth_token(client, "purge@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("p.txt", b"purge me", "text/plain")},
    )
    file_id = upload.json()["id"]

    deleted = await client.delete(f"/api/v1/files/{file_id}", headers=headers)
    assert deleted.status_code == 204

    listed = await client.get("/api/v1/files", headers=headers)
    assert listed.json() == []

    # Soft-deleted still counts toward usage
    usage = await client.get("/api/v1/files/usage", headers=headers)
    assert usage.status_code == 200
    assert usage.json()["file_count"] >= 1

    from app.main import app
    from app.core.database import get_db

    override = app.dependency_overrides.get(get_db)
    assert override is not None
    agen = override()
    db = await agen.__anext__()
    try:
        result = await db.execute(select(User).where(User.email == "purge@example.com"))
        user = result.scalar_one()
        user.is_admin = True
        from app.modules.files.models import FileRecord

        rec = (
            await db.execute(select(FileRecord).where(FileRecord.id == file_id))
        ).scalar_one()
        rec.deleted_at = datetime.now(timezone.utc) - timedelta(days=1)
        await db.commit()
    finally:
        await agen.aclose()

    purged = await client.post("/api/v1/files/admin/purge", headers=headers)
    assert purged.status_code == 200
    assert purged.json()["purged"] >= 1


@pytest.mark.asyncio
async def test_public_visibility(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))

    token = await _auth_token(client, "public@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("pub.txt", b"public data", "text/plain")},
    )
    file_id = upload.json()["id"]

    # Private by default — public route 404
    before = await client.get(f"/api/v1/files/public/{file_id}")
    assert before.status_code == 404

    patched = await client.patch(
        f"/api/v1/files/{file_id}",
        headers=headers,
        json={"visibility": "public"},
    )
    assert patched.status_code == 200
    assert patched.json()["visibility"] == "public"

    after = await client.get(f"/api/v1/files/public/{file_id}")
    assert after.status_code == 200
    assert after.content == b"public data"
    assert "public" in after.headers.get("Cache-Control", "")
