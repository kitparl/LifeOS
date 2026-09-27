"""DSA admin commands (run from backend/).

    python -m app.modules.dsa.cli grant-admin <username>
    python -m app.modules.dsa.cli revoke-admin <username>

Admins can edit the DSA catalog (statements, signatures, test cases) in the app.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User


class UserNotFoundError(LookupError):
    pass


async def set_admin(db: AsyncSession, username: str, value: bool) -> User:
    result = await db.execute(select(User).where(func.lower(User.username) == username.strip().lower()))
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError(username)
    user.is_admin = value
    await db.flush()
    return user


async def _run(username: str, value: bool) -> None:
    from app.core.database import async_session_factory, engine

    try:
        async with async_session_factory() as db:
            await set_admin(db, username, value)
            await db.commit()
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DSA admin commands")
    parser.add_argument("command", choices=["grant-admin", "revoke-admin"])
    parser.add_argument("username")
    args = parser.parse_args(argv)
    value = args.command == "grant-admin"
    try:
        asyncio.run(_run(args.username, value))
    except UserNotFoundError:
        print(f"no user named {args.username!r}", file=sys.stderr)
        return 1
    print(f"{args.username}: is_admin={value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
