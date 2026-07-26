from datetime import datetime, timezone

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User, UsernameHistory
from app.modules.auth.username_rules import normalize_username


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.username == normalize_username(username))
        )
        return result.scalar_one_or_none()

    async def get_by_identifier(self, identifier: str) -> User | None:
        value = (identifier or "").strip()
        if "@" in value:
            return await self.get_by_email(value)
        return await self.get_by_username(value)

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(
        self, email: str, hashed_password: str, display_name: str, username: str
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            display_name=display_name,
            username=normalize_username(username),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, **fields) -> User:
        for key, value in fields.items():
            if value is not None:
                setattr(user, key, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def add_username_history(
        self,
        user_id: str,
        old_username: str,
        new_username: str,
        changed_by: str,
        reason: str | None = None,
    ) -> UsernameHistory:
        entry = UsernameHistory(
            user_id=user_id,
            old_username=old_username,
            new_username=new_username,
            changed_by=changed_by,
            reason=reason,
            changed_at=datetime.now(timezone.utc),
        )
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def list_username_history(self, user_id: str) -> list[UsernameHistory]:
        result = await self.db.execute(
            select(UsernameHistory)
            .where(UsernameHistory.user_id == user_id)
            .order_by(UsernameHistory.changed_at.desc())
        )
        return list(result.scalars().all())

    async def search_users(
        self, q: str, limit: int = 20, *, include_email: bool = False
    ) -> list[User]:
        term = (q or "").strip()
        if not term:
            return []
        pattern = f"%{term.lower()}%"
        exact = normalize_username(term)
        conditions = [
            func.lower(User.username).like(pattern),
            func.lower(User.display_name).like(pattern),
        ]
        if include_email:
            conditions.append(func.lower(User.email).like(pattern))
        result = await self.db.execute(
            select(User)
            .where(or_(*conditions))
            .order_by(
                case((User.username == exact, 0), else_=1),
                User.username.asc(),
            )
            .limit(limit)
        )
        return list(result.scalars().all())
