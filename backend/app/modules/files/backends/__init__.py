from __future__ import annotations

from app.core.config import Settings, get_settings
from app.modules.files.backends.base import StorageBackend
from app.modules.files.backends.local import LocalStorageBackend
from app.modules.files.backends.s3 import S3StorageBackend


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
    name = (settings.storage_backend or "local").strip().lower()
    if name == "s3":
        return S3StorageBackend(settings)
    return LocalStorageBackend(settings.upload_dir)
