from datetime import UTC, datetime, timedelta
from typing import Any
import bcrypt
from jose import JWTError, jwt
from app.core.config import get_settings

settings = get_settings()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": subject, "exp": expire, "type": "access"}, settings.secret_key, algorithm=settings.algorithm)

def create_refresh_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode({"sub": subject, "exp": expire, "type": "refresh"}, settings.secret_key, algorithm=settings.algorithm)

def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

def verify_token_type(payload: dict[str, Any], expected: str) -> str:
    if payload.get("type") != expected:
        raise JWTError("Invalid token type")
    sub = payload.get("sub")
    if not sub:
        raise JWTError("Missing subject")
    return str(sub)
