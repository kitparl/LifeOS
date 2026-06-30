from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import RegisterRequest, UserUpdateRequest

class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def register(self, data: RegisterRequest):
        if await self.repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = await self.repo.create(data.email, hash_password(data.password), data.display_name)
        return user, create_access_token(user.id), create_refresh_token(user.id)

    async def login(self, email: str, password: str):
        user = await self.repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user, create_access_token(user.id), create_refresh_token(user.id)

    async def update_profile(self, user_id: str, data: UserUpdateRequest):
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return await self.repo.update(user, display_name=data.display_name, timezone=data.timezone)
