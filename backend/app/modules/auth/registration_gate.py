"""Session-scoped registration unlock (admin gate).

A short-lived JWT in an HttpOnly session cookie unlocks /register and admin
create-user for the current browser. No refresh — expires or is cleared.
"""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.security import verify_password

REG_UNLOCK_COOKIE = "reg_unlock"
_UNLOCK_TYPE = "reg_unlock"
_UNLOCK_TTL_HOURS = 4

settings = get_settings()


def create_unlock_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=_UNLOCK_TTL_HOURS)
    return jwt.encode(
        {"sub": "registration-gate", "exp": expire, "type": _UNLOCK_TYPE},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def verify_unlock_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("type") == _UNLOCK_TYPE
    except JWTError:
        return False


def is_registration_unlocked(request: Request) -> bool:
    token = request.cookies.get(REG_UNLOCK_COOKIE)
    if not token:
        return False
    return verify_unlock_token(token)


def require_registration_unlock(request: Request) -> None:
    if not is_registration_unlocked(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Registration is locked",
        )


def verify_gate_credentials(email: str, password: str) -> bool:
    """Check against env-configured admin gate credentials."""
    expected_email = (settings.admin_gate_email or "").strip().lower()
    password_hash = settings.admin_gate_password_hash or ""
    if not expected_email or not password_hash:
        return False
    try:
        password_ok = verify_password(password, password_hash)
    except (ValueError, TypeError):
        return False
    if email.strip().lower() != expected_email:
        return False
    return password_ok


def unlock_cookie_kwargs() -> dict:
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.cookie_secure,
        # No max_age → session cookie (cleared when browser fully closes)
    }
