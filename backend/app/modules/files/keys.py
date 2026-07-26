from __future__ import annotations

from datetime import datetime, timezone


def build_storage_key(
    *,
    module: str | None,
    entity_id: str | None,
    file_id: str,
    extension: str,
    now: datetime | None = None,
) -> str:
    """Backend-relative key identical across local and S3/R2."""
    ts = now or datetime.now(timezone.utc)
    mod = module or "_unassigned"
    ent = entity_id or "_unlinked"
    ext = extension if extension.startswith(".") or extension == "" else f".{extension}"
    return f"{mod}/{ent}/{ts.year:04d}/{ts.month:02d}/{file_id}/original{ext}"
