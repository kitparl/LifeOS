"""Edge checks for Garmin import uploads: classify by content and enforce size limits."""

from typing import Literal

from app.core.config import Settings
from app.core.exceptions import BadRequestError, PayloadTooLargeError
from app.modules.files.validation import looks_like_fit

UploadKind = Literal["fit", "zip"]

UNSUPPORTED = "Unsupported file type; upload .fit files or a Garmin export .zip"
_ZIP_MAGIC = b"PK\x03\x04"


def classify_upload(head: bytes) -> UploadKind:
    """Decide the kind from the first bytes, never from the file name."""
    if looks_like_fit(head):
        return "fit"
    if head.startswith(_ZIP_MAGIC):
        return "zip"
    raise BadRequestError(UNSUPPORTED)


def max_bytes_for(kind: UploadKind, settings: Settings) -> int:
    return settings.garmin_import_max_fit_bytes if kind == "fit" else settings.garmin_import_max_archive_bytes


def check_size(kind: UploadKind, size_bytes: int, settings: Settings) -> None:
    limit = max_bytes_for(kind, settings)
    if size_bytes > limit:
        raise PayloadTooLargeError(f"File is too large (limit {limit // (1024 * 1024)} MB)")
