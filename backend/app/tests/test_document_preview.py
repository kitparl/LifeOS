import asyncio
import io
import shutil
import zipfile
from pathlib import Path

import pytest


async def _auth_token(client, email="docpreview@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": ("usr_" + email.split("@")[0].replace(".", "")[:26]),
            "email": email,
            "password": "password123",
            "display_name": "Preview User",
        },
    )
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return res.json()["access_token"]


def _rtf_bytes(text: str = "Hello LifeOS") -> bytes:
    return ("{\\rtf1\\ansi " + text + "}").encode("ascii")


async def _wait_until_ready_or_failed(client, headers, file_id, *, attempts=50):
    body = None
    for _ in range(attempts):
        res = await client.get(f"/api/v1/files/{file_id}/preview-info", headers=headers)
        body = res.json()
        if body["status"] in ("ready", "failed"):
            return body
        await asyncio.sleep(0.02)
    raise AssertionError(f"preview never settled: {body}")


@pytest.mark.asyncio
async def test_preview_info_unauthenticated_401(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))
    res = await client.get("/api/v1/files/does-not-exist/preview-info")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_preview_and_download_other_user_404(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))

    owner_token = await _auth_token(client, "owner@example.com")
    other_token = await _auth_token(client, "other@example.com")

    upload = await client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        files={"file": ("note.txt", b"secret text", "text/plain")},
    )
    file_id = upload.json()["id"]

    other_headers = {"Authorization": f"Bearer {other_token}"}
    assert (await client.get(f"/api/v1/files/{file_id}/preview-info", headers=other_headers)).status_code == 404
    assert (await client.get(f"/api/v1/files/{file_id}/preview", headers=other_headers)).status_code == 404
    assert (await client.get(f"/api/v1/files/{file_id}/download", headers=other_headers)).status_code == 404


@pytest.mark.asyncio
async def test_preview_info_native_pdf_ready_immediately(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))
    token = await _auth_token(client, "pdfuser@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("doc.pdf", b"%PDF-1.4 minimal", "application/pdf")},
    )
    file_id = upload.json()["id"]

    info = await client.get(f"/api/v1/files/{file_id}/preview-info", headers=headers)
    assert info.status_code == 200
    body = info.json()
    assert body["preview_type"] == "pdf"
    assert body["status"] == "ready"
    assert body["preview_url"] == f"/api/v1/files/{file_id}/preview"
    assert body["download_url"] == f"/api/v1/files/{file_id}/download"

    preview = await client.get(f"/api/v1/files/{file_id}/preview", headers=headers)
    assert preview.status_code == 200
    assert "inline" in preview.headers["content-disposition"]

    download = await client.get(f"/api/v1/files/{file_id}/download", headers=headers)
    assert download.status_code == 200
    assert "attachment" in download.headers["content-disposition"]


@pytest.mark.asyncio
async def test_preview_info_unsupported_type(client, tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))
    token = await _auth_token(client, "zip@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(get_settings(), "allowed_upload_types", get_settings().allowed_upload_types + ",application/zip")

    upload = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("archive.zip", b"PK\x05\x06" + b"\x00" * 18, "application/zip")},
    )
    assert upload.status_code == 201
    file_id = upload.json()["id"]

    info = await client.get(f"/api/v1/files/{file_id}/preview-info", headers=headers)
    body = info.json()
    assert body["preview_type"] == "unsupported"
    assert body["status"] == "ready"
    assert body["preview_url"] is None

    preview = await client.get(f"/api/v1/files/{file_id}/preview", headers=headers)
    assert preview.status_code == 404


@pytest.mark.asyncio
async def test_office_conversion_success_and_cache_hit(client, tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.modules.files.preview import office_converter

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(get_settings(), "preview_cache_dir", str(tmp_path / "preview-cache"))

    calls = {"count": 0}

    async def fake_convert(input_path: Path, *, timeout_seconds: int) -> bytes:
        calls["count"] += 1
        return b"%PDF-1.4 fake converted pdf"

    monkeypatch.setattr(office_converter, "convert_to_pdf", fake_convert)
    monkeypatch.setattr("app.modules.files.preview_service.convert_to_pdf", fake_convert)

    token = await _auth_token(client, "office@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("letter.rtf", _rtf_bytes(), "application/rtf")},
    )
    assert upload.status_code == 201
    file_id = upload.json()["id"]

    first = await _wait_until_ready_or_failed(client, headers, file_id)
    assert first["status"] == "ready"
    assert first["preview_type"] == "pdf"
    assert calls["count"] == 1

    preview = await client.get(f"/api/v1/files/{file_id}/preview", headers=headers)
    assert preview.status_code == 200
    assert preview.content == b"%PDF-1.4 fake converted pdf"

    # Second preview-info call is a cache hit — no second conversion.
    second = await client.get(f"/api/v1/files/{file_id}/preview-info", headers=headers)
    assert second.json()["status"] == "ready"
    assert calls["count"] == 1

    # Range request against the cached converted PDF.
    ranged = await client.get(
        f"/api/v1/files/{file_id}/preview",
        headers={**headers, "Range": "bytes=0-4"},
    )
    assert ranged.status_code == 206
    assert ranged.content == b"%PDF-"


@pytest.mark.asyncio
async def test_office_conversion_failure_reports_failed_without_path_leak(client, tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.modules.files.preview import office_converter
    from app.modules.files.preview.office_converter import ConversionError

    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(get_settings(), "upload_dir", str(upload_dir))
    monkeypatch.setattr(get_settings(), "preview_cache_dir", str(tmp_path / "preview-cache"))

    async def failing_convert(input_path: Path, *, timeout_seconds: int) -> bytes:
        raise ConversionError("Document conversion failed")

    monkeypatch.setattr(office_converter, "convert_to_pdf", failing_convert)
    monkeypatch.setattr("app.modules.files.preview_service.convert_to_pdf", failing_convert)

    token = await _auth_token(client, "failconv@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("bad.rtf", _rtf_bytes("failure path content"), "application/rtf")},
    )
    file_id = upload.json()["id"]

    result = await _wait_until_ready_or_failed(client, headers, file_id)
    assert result["status"] == "failed"
    assert result["error"] == "Document conversion failed"
    assert str(upload_dir) not in result["error"]
    assert "/" not in result["error"] or "uploads" not in result["error"]

    preview = await client.get(f"/api/v1/files/{file_id}/preview", headers=headers)
    assert preview.status_code == 409


@pytest.mark.asyncio
async def test_preview_max_file_size_skips_conversion(client, tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.modules.files.preview import office_converter

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(get_settings(), "preview_max_file_bytes", 5)

    called = {"yes": False}

    async def should_not_run(input_path: Path, *, timeout_seconds: int) -> bytes:
        called["yes"] = True
        return b""

    monkeypatch.setattr(office_converter, "convert_to_pdf", should_not_run)
    monkeypatch.setattr("app.modules.files.preview_service.convert_to_pdf", should_not_run)

    token = await _auth_token(client, "toolarge@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("letter.rtf", _rtf_bytes("this rtf body is long enough to exceed the tiny limit"), "application/rtf")},
    )
    file_id = upload.json()["id"]

    info = await client.get(f"/api/v1/files/{file_id}/preview-info", headers=headers)
    body = info.json()
    assert body["preview_type"] == "unsupported"
    assert body["error"] == "File too large to preview"
    await asyncio.sleep(0.05)
    assert called["yes"] is False


def test_verify_ooxml_structure(tmp_path):
    from app.modules.files.preview.ooxml import verify_ooxml_structure

    good = tmp_path / "good.docx"
    with zipfile.ZipFile(good, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", "<w:document/>")
    assert verify_ooxml_structure(good) is True

    missing_kind_folder = tmp_path / "spoofed.docx"
    with zipfile.ZipFile(missing_kind_folder, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("random/file.txt", "not an office document")
    assert verify_ooxml_structure(missing_kind_folder) is False

    not_a_zip = tmp_path / "garbage.docx"
    not_a_zip.write_bytes(b"this is not a zip file at all")
    assert verify_ooxml_structure(not_a_zip) is False


@pytest.mark.asyncio
async def test_ooxml_mismatch_marks_preview_failed(client, tmp_path, monkeypatch):
    """A FileRecord claiming an OOXML mime type whose bytes don't match the
    real inner structure (e.g. a DB row that predates stricter validation,
    or a corrupted upload) must fail conversion cleanly, never crash or leak
    a filesystem path."""
    from app.core.config import get_settings
    from app.core.database import get_db
    from app.main import app
    from app.modules.files.backends.local import LocalStorageBackend
    from app.modules.files.keys import build_storage_key
    from app.modules.files.models import FileRecord

    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(get_settings(), "upload_dir", str(upload_dir))
    monkeypatch.setattr(get_settings(), "preview_cache_dir", str(tmp_path / "preview-cache"))

    token = await _auth_token(client, "ooxmlmismatch@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Seed a FileRecord + on-disk bytes directly (bypassing upload validation)
    # whose zip lacks the word/ prefix despite claiming to be a .docx.
    override = app.dependency_overrides.get(get_db)
    agen = override()
    db = await agen.__anext__()
    try:
        from app.modules.auth.models import User
        from sqlalchemy import select

        user = (
            await db.execute(select(User).where(User.email == "ooxmlmismatch@example.com"))
        ).scalar_one()

        backend = LocalStorageBackend(upload_dir)
        key = build_storage_key(module=None, entity_id=None, file_id="spoofed-1", extension=".docx")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")

        async def _one_chunk():
            yield buf.getvalue()

        stored = await backend.save(key, _one_chunk(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        record = FileRecord(
            id="spoofed-1",
            user_id=user.id,
            filename="spoofed.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=stored.size_bytes,
            storage_backend="local",
            storage_key=key,
            url="/api/v1/files/spoofed-1/content",
            checksum_sha256=stored.checksum_sha256,
            extension="docx",
        )
        db.add(record)
        await db.commit()
    finally:
        await agen.aclose()

    result = await _wait_until_ready_or_failed(client, headers, "spoofed-1")
    assert result["status"] == "failed"
    assert str(upload_dir) not in (result["error"] or "")


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice not installed on this host")
@pytest.mark.asyncio
async def test_real_libreoffice_conversion(tmp_path):
    from app.modules.files.preview.office_converter import convert_to_pdf

    src = tmp_path / "sample.rtf"
    src.write_bytes(_rtf_bytes("Real conversion smoke test"))

    pdf_bytes = await convert_to_pdf(src, timeout_seconds=30)
    assert pdf_bytes.startswith(b"%PDF")
