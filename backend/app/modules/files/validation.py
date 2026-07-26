from __future__ import annotations

from pathlib import PurePosixPath

import filetype
from fastapi import HTTPException, status

from app.core.config import Settings, get_settings

ALLOWED_MODULES = frozenset(
    {
        "tasks",
        "habits",
        "goals",
        "journal",
        "routines",
        "knowledge_notes",
        "ocr",
        "running",
        "finance",
        "wishlist",
        "career",
        "learning",
        "mood",
        "memory",
        "calendar",
        "voice",
        "telegram",
        "general",
    }
)

# Extension → MIME for types filetype cannot sniff (plain text family).
_TEXT_EXT_MIME = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".csv": "text/csv",
}

# Sniffed MIME → preferred extension (server-generated keys never use client filename).
_MIME_TO_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/csv": ".csv",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "audio/mp4": ".m4a",
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
    "audio/x-m4a": ".m4a",
}

# Client extension must not contradict these sniffed types.
_EXT_EXPECTED_MIME: dict[str, set[str]] = {
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".webp": {"image/webp"},
    ".gif": {"image/gif"},
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain"},
    ".md": {"text/markdown", "text/plain"},
    ".markdown": {"text/markdown", "text/plain"},
    ".csv": {"text/csv", "text/plain"},
    ".html": set(),  # never allowed inline; rejected if sniffed as html
    ".htm": set(),
    ".svg": set(),
    ".mp3": {"audio/mpeg"},
    ".m4a": {"audio/mp4", "audio/x-m4a"},
    ".ogg": {"audio/ogg"},
    ".webm": {"audio/webm", "video/webm"},
}

INLINE_SAFE_TYPES = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
        "application/pdf",
    }
)

NEVER_INLINE_TYPES = frozenset(
    {
        "text/html",
        "application/xhtml+xml",
        "image/svg+xml",
    }
)


def parse_allowed_types(settings: Settings | None = None) -> set[str]:
    settings = settings or get_settings()
    return {t.strip().lower() for t in settings.allowed_upload_types.split(",") if t.strip()}


def validate_module(module: str | None) -> str | None:
    if module is None or module == "":
        return None
    if module not in ALLOWED_MODULES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid module '{module}'. Allowed: {', '.join(sorted(ALLOWED_MODULES))}",
        )
    return module


def extension_for_mime(content_type: str) -> str:
    return _MIME_TO_EXT.get(content_type.lower(), "")


def sniff_content_type(head_bytes: bytes, filename: str, settings: Settings | None = None) -> str:
    """Sniff real type from magic bytes; fall back for text; enforce allowlist."""
    settings = settings or get_settings()
    allowed = parse_allowed_types(settings)
    client_ext = PurePosixPath(filename).suffix.lower()

    kind = filetype.guess(head_bytes) if head_bytes else None
    sniffed: str | None = kind.mime if kind else None

    if sniffed is None:
        # Text family: filetype cannot sniff; require UTF-8-decodable head + known ext.
        if client_ext in _TEXT_EXT_MIME:
            try:
                head_bytes.decode("utf-8")
                sniffed = _TEXT_EXT_MIME[client_ext]
            except UnicodeDecodeError:
                sniffed = "application/octet-stream"
        else:
            sniffed = "application/octet-stream"

    sniffed = sniffed.lower()

    if sniffed in NEVER_INLINE_TYPES or client_ext in {".html", ".htm", ".svg"}:
        # Reject HTML/SVG uploads entirely when not on allowlist (they never are by default).
        if sniffed not in allowed:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{sniffed}' is not allowed",
            )

    if sniffed not in allowed and sniffed != "application/octet-stream":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{sniffed}' is not allowed",
        )
    if sniffed == "application/octet-stream" and "application/octet-stream" not in allowed:
        # Binary unknown — reject unless explicitly allowed.
        if client_ext not in _TEXT_EXT_MIME:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Could not determine an allowed file type",
            )

    expected = _EXT_EXPECTED_MIME.get(client_ext)
    if expected is not None and expected and sniffed not in expected:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"File content ({sniffed}) does not match extension '{client_ext}'",
        )
    if expected is not None and not expected:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Extension '{client_ext}' is not allowed",
        )

    return sniffed
