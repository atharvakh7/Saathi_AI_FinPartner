"""/plan/* and /risk/* endpoints (spec §7.2, §7.4)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rate_limit import rate_limit
from app.core.security import get_current_user
from app.core.types import MonthStr, month_bounds
from app.modules.planner import service
from app.modules.planner.data import load_inputs
from app.modules.planner.schemas import (
    BudgetOut,
    BudgetRegenerateOut,
    EmergencyFundIn,
    EmergencyFundOut,
    ForecastMonthOut,
    IncomeMonthOut,
    OverviewOut,
    RiskHistoryItem,
    RiskOut,
)
from app.modules.users.models import User

router = APIRouter(prefix="/plan", tags=["planner"])
risk_router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/overview", response_model=OverviewOut)
async def plan_overview(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.overview(session, user)


@router.get("/income-history", response_model=list[IncomeMonthOut])
async def income_history(
    months: int = Query(default=12, ge=1, le=24),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return service.income_history(await load_inputs(session, user.id), months)


@router.get("/forecast", response_model=list[ForecastMonthOut])
async def plan_forecast(
    months: int = Query(default=6, ge=1, le=12),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await service.stored_forecast(session, await load_inputs(session, user.id), months)


@router.get("/budget", response_model=BudgetOut)
async def plan_budget(
    month: MonthStr | None = None, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    inputs = await load_inputs(session, user.id)
    return await service.get_budget(session, inputs, month_bounds(month)[0])


@router.post(
    "/budget/regenerate", response_model=BudgetRegenerateOut,
    dependencies=[Depends(rate_limit("plan_regenerate", 6, 3600))],
)
async def regenerate_budget(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return BudgetRegenerateOut(budget=await service.regenerate_budget(session, user))


@router.get("/emergency-fund", response_model=EmergencyFundOut)
async def get_emergency_fund(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.get_emergency_fund(session, user)


@router.put("/emergency-fund", response_model=EmergencyFundOut)
async def put_emergency_fund(
    body: EmergencyFundIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    return await service.put_emergency_fund(session, user, body.target_months)


@risk_router.get("/current", response_model=RiskOut)
async def risk_current(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.current_risk(session, user)


@risk_router.get("/history", response_model=list[RiskHistoryItem])
async def risk_history(
    days: int = Query(default=90, ge=1, le=365),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await service.risk_history(session, user, days)
