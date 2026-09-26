from __future__ import annotations

from typing import Literal

from app.core.config import Settings, get_settings
from app.modules.files.backends.base import StorageBackend
from app.modules.files.backends.local import LocalStorageBackend
from app.modules.files.backends.s3 import S3StorageBackend


def default_backend_name(settings: Settings) -> Literal["local", "s3"]:
    """Configured backend for new writes; anything unrecognised means local disk."""
    name = (settings.storage_backend or "local").strip().lower()
    return "s3" if name == "s3" else "local"


def resolve_backend(name: str, settings: Settings | None = None) -> StorageBackend:
    """Resolve a backend by per-row storage_backend name (dual-read for migration)."""
    settings = settings or get_settings()
    if name == "s3":
        return S3StorageBackend(settings)
    return LocalStorageBackend(settings.upload_dir)


def get_storage_backend() -> StorageBackend:
    """FastAPI dependency: config-driven default for *new* writes.

    Constructed per-call from get_settings() so test monkeypatches of upload_dir work.
    """
    settings = get_settings()
    return resolve_backend(default_backend_name(settings), settings)
