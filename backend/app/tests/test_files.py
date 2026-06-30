import pytest


async def _auth_token(client, email="files@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Files User"},
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
