from fastapi import APIRouter, Depends, Request, Response, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, decode_token, verify_token_type
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse, UserUpdateRequest
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
REFRESH_COOKIE = "refresh_token"

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user, access, refresh = await service.register(data)
    response.set_cookie(REFRESH_COOKIE, refresh, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 7)
    return TokenResponse(access_token=access)

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user, access, refresh = await service.login(data.email, data.password)
    response.set_cookie(REFRESH_COOKIE, refresh, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 7)
    return TokenResponse(access_token=access)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response):
    from fastapi import Request
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = decode_token(token)
        user_id = verify_token_type(payload, "refresh")
    except JWTError:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    access = create_access_token(user_id)
    return TokenResponse(access_token=access)

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE)
    return {"ok": True}

@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user

@router.patch("/me", response_model=UserResponse)
async def update_me(data: UserUpdateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    updated = await service.update_profile(user.id, data)
    return updated
