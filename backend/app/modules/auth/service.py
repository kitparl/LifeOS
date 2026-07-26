from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import RegisterRequest, UserUpdateRequest, UsernameChangeRequest
from app.modules.auth.username_rules import normalize_username, validate_username


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)
        self.db = db

    async def register(self, data: RegisterRequest):
        if await self.repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        if await self.repo.get_by_username(data.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
        try:
            user = await self.repo.create(
                data.email,
                hash_password(data.password),
                data.display_name,
                data.username,
            )
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already registered",
            ) from None
        return user, create_access_token(user.id), create_refresh_token(user.id)

    async def login(self, identifier: str, password: str):
        user = await self.repo.get_by_identifier(identifier)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user, create_access_token(user.id), create_refresh_token(user.id)

    async def update_profile(self, user_id: str, data: UserUpdateRequest):
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return await self.repo.update(user, display_name=data.display_name, timezone=data.timezone)

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
        await self.repo.update(user, hashed_password=hash_password(new_password))

    async def check_username_availability(
        self, username: str, *, exclude_user_id: str | None = None
    ) -> tuple[str, bool, str | None]:
        try:
            normalized = validate_username(username)
        except ValueError as e:
            return normalize_username(username) or username, False, str(e)
        existing = await self.repo.get_by_username(normalized)
        if existing is not None and existing.id != exclude_user_id:
            return normalized, False, "Username already taken"
        return normalized, True, None

    async def change_username(self, user_id: str, data: UsernameChangeRequest):
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        new_username = data.username  # already validated/normalized by schema
        if new_username == user.username:
            return user
        taken = await self.repo.get_by_username(new_username)
        if taken is not None and taken.id != user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
        old = user.username
        try:
            user = await self.repo.update(
                user,
                username=new_username,
                username_changed_at=datetime.now(timezone.utc),
                username_change_count=(user.username_change_count or 0) + 1,
            )
            await self.repo.add_username_history(
                user_id=user.id,
                old_username=old,
                new_username=new_username,
                changed_by=user.id,
                reason=data.reason,
            )
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            ) from None
        return user

    async def list_username_history(self, user_id: str):
        return await self.repo.list_username_history(user_id)

    async def search_users(self, q: str, limit: int, *, include_email: bool):
        return await self.repo.search_users(q, limit=limit, include_email=include_email)
