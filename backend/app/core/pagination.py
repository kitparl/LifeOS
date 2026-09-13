from dataclasses import dataclass

from fastapi import Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

DEFAULT_LIMIT = 25
MAX_LIMIT = 100


@dataclass(frozen=True)
class Pagination:
    limit: int
    offset: int


def pagination_params(
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> Pagination:
    return Pagination(limit=limit, offset=offset)


async def paginate(
    db: AsyncSession,
    stmt: Select,
    pagination: Pagination,
    *,
    unique: bool = False,
) -> tuple[list, int]:
    """Run a count query plus a limited/offset query for the given select statement."""
    total = (
        await db.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))
    ).scalar_one()
    page_stmt = stmt.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(page_stmt)
    scalars = result.scalars()
    rows = scalars.unique().all() if unique else scalars.all()
    return list(rows), int(total)
