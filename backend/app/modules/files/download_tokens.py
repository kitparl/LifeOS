from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import Settings, get_settings


def mint_download_token(
    file_id: str,
    user_id: str,
    settings: Settings | None = None,
) -> tuple[str, datetime]:
    settings = settings or get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.download_token_ttl_seconds)
    token = jwt.encode(
        {
            "sub": user_id,
            "file_id": file_id,
            "exp": expires_at,
            "type": "file_download",
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return token, expires_at


def verify_download_token(
    token: str,
    file_id: str,
    settings: Settings | None = None,
) -> str:
    """Validate token scoped to file_id. Returns user_id (sub)."""
    settings = settings or get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise ValueError("Invalid download token") from exc
    if payload.get("type") != "file_download":
        raise ValueError("Invalid download token type")
    if payload.get("file_id") != file_id:
        raise ValueError("Download token not scoped to this file")
    sub = payload.get("sub")
    if not sub:
        raise ValueError("Missing subject")
    return str(sub)
