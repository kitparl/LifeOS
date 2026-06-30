from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.predictions.schemas import PredictionsSummary
from app.modules.predictions.service import PredictionsService

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/summary", response_model=PredictionsSummary)
async def predictions_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PredictionsService(db).summary(user.id)
