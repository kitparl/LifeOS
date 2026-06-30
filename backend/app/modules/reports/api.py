from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.reports.service import ReportResponse, ReportsService, ReviewResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly", response_model=ReportResponse)
async def weekly_report(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ReportsService(db).generate_report(user.id, "weekly")


@router.get("/monthly", response_model=ReportResponse)
async def monthly_report(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ReportsService(db).generate_report(user.id, "monthly")


@router.get("/yearly", response_model=ReportResponse)
async def yearly_report(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ReportsService(db).generate_report(user.id, "yearly")


@router.post("/reviews/{review_type}", response_model=ReviewResponse)
async def ai_review(
    review_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if review_type not in ("daily", "weekly", "monthly"):
        review_type = "weekly"
    return await ReportsService(db).generate_review(user.id, review_type)
