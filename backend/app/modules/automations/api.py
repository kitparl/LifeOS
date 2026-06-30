from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.automations.schemas import (
    AutomationCreate,
    AutomationEvaluateResponse,
    AutomationResponse,
    AutomationUpdate,
)
from app.modules.automations.service import AutomationService

router = APIRouter(prefix="/automations", tags=["automations"])


@router.get("/rules", response_model=list[AutomationResponse])
async def list_automations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AutomationService(db).list_rules(user.id)


@router.post("/rules", response_model=AutomationResponse, status_code=status.HTTP_201_CREATED)
async def create_automation(
    data: AutomationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AutomationService(db).create_rule(user.id, data)


@router.patch("/rules/{rule_id}", response_model=AutomationResponse)
async def update_automation(
    rule_id: str,
    data: AutomationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AutomationService(db).update_rule(user.id, rule_id, data)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    rule_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await AutomationService(db).delete_rule(user.id, rule_id)


@router.post("/evaluate", response_model=AutomationEvaluateResponse)
async def evaluate_automations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AutomationService(db).evaluate(user.id)
