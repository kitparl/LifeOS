import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_token_type
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
    UsernameAvailabilityResponse,
    UsernameChangeRequest,
    UsernameHistoryEntry,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
REFRESH_COOKIE = "refresh_token"
settings = get_settings()

_REFRESH_MAX_AGE = 60 * 60 * 24 * settings.refresh_token_expire_days

# Simple in-memory sliding window: IP -> list of request timestamps (last 60s)
_AVAIL_HITS: dict[str, list[float]] = defaultdict(list)
_AVAIL_LIMIT = 30
_AVAIL_WINDOW_S = 60.0


def _cookie_kwargs() -> dict:
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.cookie_secure,
    }


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=_REFRESH_MAX_AGE,
        **_cookie_kwargs(),
    )


def _check_availability_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    hits = [t for t in _AVAIL_HITS[ip] if now - t < _AVAIL_WINDOW_S]
    if len(hits) >= _AVAIL_LIMIT:
        _AVAIL_HITS[ip] = hits
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many availability checks. Try again shortly.",
        )
    hits.append(now)
    _AVAIL_HITS[ip] = hits


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user, access, refresh = await service.register(data)
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user, access, refresh = await service.login(data.identifier, data.password)
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    try:
        payload = decode_token(token)
        user_id = verify_token_type(payload, "refresh")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)
    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(access_token=new_access)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE, secure=settings.cookie_secure, samesite="lax")
    return {"ok": True}


@router.get("/username-available", response_model=UsernameAvailabilityResponse)
async def username_available(
    request: Request,
    username: str = Query(min_length=1, max_length=30),
    db: AsyncSession = Depends(get_db),
):
    _check_availability_rate_limit(request)
    service = AuthService(db)
    normalized, available, reason = await service.check_username_availability(username)
    return UsernameAvailabilityResponse(username=normalized, available=available, reason=reason)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    updated = await service.update_profile(user.id, data)
    return updated


@router.patch("/me/username", response_model=UserResponse)
async def change_username(
    data: UsernameChangeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.change_username(user.id, data)


@router.get("/me/username-history", response_model=list[UsernameHistoryEntry])
async def username_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.list_username_history(user.id)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.change_password(user.id, data.current_password, data.new_password)
