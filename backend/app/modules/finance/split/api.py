"""Split Bills HTTP API. Public: a missing Bearer token is a guest; a bad one is still 401."""

from fastapi import APIRouter, Depends, Header, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_optional_user
from app.core.rate_limit import SlidingWindowLimiter, enforce_ip_limit
from app.modules.auth.models import User
from app.modules.finance.split.codes import SHORT_CODE_PATTERN
from app.modules.finance.split.schemas import GroupCreate, GroupView, SeatIssued
from app.modules.finance.split.service import SplitService

router = APIRouter(prefix="/splits", tags=["splits"])

GroupCode = Path(pattern=SHORT_CODE_PATTERN)
SeatSecret = Header(default=None, alias="X-Split-Seat", max_length=64)

# Per-client-IP sliding windows for the unauthenticated write endpoints.
_create_limiter = SlidingWindowLimiter(limit=10, window_seconds=600.0)


def reset_limiters() -> None:
    """Forget rate-limit history (tests)."""
    _create_limiter.reset()


@router.post("/groups", response_model=SeatIssued, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    enforce_ip_limit(_create_limiter, request, "Too many groups created. Try again later.")
    return await SplitService(db).create_group(data, user)


@router.get("/groups/{code}", response_model=GroupView)
async def get_group(
    code: str = GroupCode,
    seat: str | None = SeatSecret,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    return await SplitService(db).get_group(code, seat, user)
