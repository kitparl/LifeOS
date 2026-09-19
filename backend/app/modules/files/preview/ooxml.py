from __future__ import annotations

import zipfile
from pathlib import Path

# OOXML (docx/xlsx/pptx) content-type prefixes that must be present inside
# the ZIP for the format to be genuine (defense-in-depth check right before
# handing a file to LibreOffice — content_type on FileRecord is already
# server-sniffed at upload, this guards the conversion step independently).
_OOXML_REQUIRED_ENTRY = "[Content_Types].xml"
_OOXML_KIND_PREFIXES = ("word/", "xl/", "ppt/")

_OOXML_MIME_TYPES = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
)


def is_ooxml_mime(content_type: str) -> bool:
    return content_type in _OOXML_MIME_TYPES


def verify_ooxml_structure(path: Path) -> bool:
    """True if `path` is a well-formed OOXML zip with the expected inner layout.

    Never raises on malformed/corrupt input — callers treat a False result as
    "not a genuine OOXML file" (unsupported / download-only), never as a
    server error.
    """
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
    except (zipfile.BadZipFile, OSError):
        return False

    if _OOXML_REQUIRED_ENTRY not in names:
        return False
    return any(name.startswith(prefix) for name in names for prefix in _OOXML_KIND_PREFIXES)
