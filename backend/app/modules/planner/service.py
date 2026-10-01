"""Planner orchestration: regenerate, overview, budget, emergency fund, risk (spec §5.5, §7.4).

`regenerate()` recomputes forecast + current/next budget + emergency fund + today's risk snapshot.
It runs on demand (POST /plan/budget/regenerate) and after transaction, debt, goal and profile
changes (event handlers below). Step 17 moves the event-driven runs to debounced Celery jobs and
adds the daily 02:00/03:00 IST schedules.
"""

import logging
import statistics
import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import events
from app.core.db import SessionLocal
from app.core.errors import AppError
from app.core.types import add_months, today_ist
from app.modules.finance.service import invalidate_summary
from app.modules.planner import emergency, risk
from app.modules.planner.budget import compute_budget, store_budget
from app.modules.planner.data import PlanInputs, load_inputs
from app.modules.planner.forecast import forecast, income_stats, store_forecast
from app.modules.planner.models import Budget, CashflowForecast, RiskSnapshot
from app.modules.planner.schemas import (
    BudgetOut,
    EmergencyFundOut,
    EmergencyOverviewOut,
    ForecastMonthOut,
    IncomeMonthOut,
    OverviewOut,
    PatternOut,
    RiskComponentOut,
    RiskHistoryItem,
    RiskOut,
)
from app.modules.users.models import User

log = logging.getLogger(__name__)

HISTORY_SHOWN = 12
PATTERN_BY_DECLARED = {"fixed_monthly": "steady", "irregular": "ups_and_downs", "seasonal": "seasonal"}


def _ym(d: date) -> str:
    return f"{d:%Y-%m}"


# --- Regenerate --------------------------------------------------------------------

async def regenerate(session: AsyncSession, user_id: uuid.UUID) -> PlanInputs:
    inputs = await load_inputs(session, user_id)
    await store_forecast(session, inputs, forecast(inputs))
    current_plan = compute_budget(inputs, inputs.current_month)
    await store_budget(session, inputs, current_plan)
    await store_budget(session, inputs, compute_budget(inputs, add_months(inputs.current_month, 1)))
    if inputs.ef_plan is not None:
        figures = emergency.compute(inputs, current_plan.savings_target)
        if figures.target_amount > 0:
            await emergency.upsert_plan(session, inputs, figures, create=False)
    result = risk.compute_risk(inputs)
    if result is not None:
        await risk.store_snapshot(session, inputs, result)
    await session.commit()
    await invalidate_summary(user_id)
    return inputs


@events.on(events.PROFILE_UPDATED)
@events.on(events.ONBOARDING_COMPLETED)
@events.on(events.TRANSACTIONS_CHANGED)
@events.on(events.DEBTS_CHANGED)
@events.on(events.GOALS_CHANGED)
async def regenerate_after_change(user_id: uuid.UUID) -> None:
    async with SessionLocal() as session:
        await regenerate(session, user_id)


# --- Budget ------------------------------------------------------------------------

def _budget_out(row: Budget, inputs: PlanInputs) -> BudgetOut:
    t = inputs.totals(row.month)
    return BudgetOut(
        month=_ym(row.month),
        mode=row.mode,
        expected_income_inr=row.expected_income_inr,
        planning_income_inr=row.planning_income_inr,
        needs_limit_inr=row.needs_limit_inr,
        wants_limit_inr=row.wants_limit_inr,
        savings_target_inr=row.savings_target_inr,
        spent_needs_inr=t.essential,
        spent_wants_inr=t.nonessential,
        saved_so_far_inr=t.income - t.expense,
        generated_at=row.generated_at,
    )


async def get_budget(session: AsyncSession, inputs: PlanInputs, month: date) -> BudgetOut:
    """Stored budget for the month, computed and stored if absent (spec §7.4)."""
    row = (
        await session.execute(select(Budget).where(Budget.user_id == inputs.user_id, Budget.month == month))
    ).scalar_one_or_none()
    if row is None:
        row = await store_budget(session, inputs, compute_budget(inputs, month))
        await session.commit()
    return _budget_out(row, inputs)


async def regenerate_budget(session: AsyncSession, user: User) -> BudgetOut:
    inputs = await regenerate(session, user.id)
    return await get_budget(session, inputs, inputs.current_month)


# --- Overview, history, forecast ---------------------------------------------------

def pattern(inputs: PlanInputs) -> PatternOut:
    n, mean, sigma = income_stats(inputs)
    if n >= 3 and mean:
        cv = sigma / mean
        label = "steady" if cv < 0.25 else "ups_and_downs" if cv < 0.5 else "seasonal"
    else:
        cv = risk.PATTERN_CV.get(inputs.income_pattern, risk.DEFAULT_CV)
        label = PATTERN_BY_DECLARED.get(inputs.income_pattern, "ups_and_downs")
    return PatternOut(label=label, cv=round(cv, 2), months_of_data=n)


def income_history(inputs: PlanInputs, months: int = HISTORY_SHOWN) -> list[IncomeMonthOut]:
    shown = [add_months(inputs.current_month, -i) for i in range(months - 1, -1, -1)]  # oldest first, incl. current
    with_data = [inputs.totals(m).income for m in shown if inputs.totals(m).income_count]
    mean = statistics.mean(with_data) if with_data else 0.0
    out = []
    for m in shown:
        income = inputs.totals(m).income
        # The current month is still in progress, so it is never flagged lean.
        lean = mean > 0 and m != inputs.current_month and income < 0.7 * mean
        out.append(IncomeMonthOut(month=_ym(m), income_inr=income, is_lean=lean))
    return out


async def stored_forecast(session: AsyncSession, inputs: PlanInputs, months: int) -> list[ForecastMonthOut]:
    first, last = add_months(inputs.current_month, 1), add_months(inputs.current_month, months)
    rows = list(
        (
            await session.execute(
                select(CashflowForecast)
                .where(CashflowForecast.user_id == inputs.user_id, CashflowForecast.month.between(first, last))
                .order_by(CashflowForecast.month)
            )
        ).scalars()
    )
    if len(rows) < months:
        items = forecast(inputs, max(months, 6))
        await store_forecast(session, inputs, items)
        await session.commit()
        return [_forecast_out(f.month, f.expected_income, f.lower_income, f.upper_income, f.expected_expense,
                              f.expected_net, f.mode, f.confidence) for f in items[:months]]
    return [_forecast_out(r.month, r.expected_income_inr, r.lower_income_inr, r.upper_income_inr,
                          r.expected_expense_inr, r.expected_net_inr, r.mode, r.confidence) for r in rows]


def _forecast_out(month, exp, lo, hi, expense, net, mode, conf) -> ForecastMonthOut:
    return ForecastMonthOut(month=_ym(month), expected_income_inr=exp, lower_income_inr=lo, upper_income_inr=hi,
                            expected_expense_inr=expense, expected_net_inr=net, mode=mode, confidence=conf)


async def overview(session: AsyncSession, user: User) -> OverviewOut:
    inputs = await load_inputs(session, user.id)
    fc = await stored_forecast(session, inputs, 6)
    budget = await get_budget(session, inputs, inputs.current_month)
    ef = emergency.compute(inputs, float(budget.savings_target_inr))
    return OverviewOut(
        has_data=inputs.has_any_data,
        pattern=pattern(inputs),
        income_history=income_history(inputs),
        forecast=fc,
        current_budget=budget,
        emergency_fund=EmergencyOverviewOut(
            exists=ef.exists, target_inr=ef.target_amount, current_inr=ef.current_amount, pct=ef.pct
        ),
        tight_months=[f.month for f in fc if f.mode == "lean"],
        data_confidence=fc[0].confidence if fc else "low",
    )


# --- Emergency fund ----------------------------------------------------------------

def _emergency_out(f: emergency.EmergencyFigures) -> EmergencyFundOut:
    return EmergencyFundOut(
        exists=f.exists,
        target_months=f.target_months,
        monthly_essential_expense_inr=f.monthly_essential,
        target_amount_inr=f.target_amount,
        current_amount_inr=f.current_amount,
        pct=f.pct,
        suggested_monthly_contribution_inr=f.suggested_monthly,
        estimated_completion_date=f.estimated_completion,
        goal_id=f.goal_id,
    )


async def get_emergency_fund(session: AsyncSession, user: User) -> EmergencyFundOut:
    """The plan if it exists, otherwise a computed suggestion with exists=false (spec S21)."""
    inputs = await load_inputs(session, user.id)
    budget = await get_budget(session, inputs, inputs.current_month)
    return _emergency_out(emergency.compute(inputs, float(budget.savings_target_inr)))


async def put_emergency_fund(session: AsyncSession, user: User, target_months: int) -> EmergencyFundOut:
    """Create the plan (and its goal, or link an existing emergency-fund goal) or change target_months."""
    inputs = await load_inputs(session, user.id)
    budget = compute_budget(inputs, inputs.current_month)
    figures = emergency.compute(inputs, budget.savings_target, target_months)
    await emergency.upsert_plan(session, inputs, figures, create=True)
    await session.commit()
    # The plan changes the risk score and the budget's savings rate.
    inputs = await regenerate(session, user.id)
    budget_row = await get_budget(session, inputs, inputs.current_month)
    return _emergency_out(emergency.compute(inputs, float(budget_row.savings_target_inr)))


# --- Risk --------------------------------------------------------------------------

def _risk_out(snap: RiskSnapshot) -> RiskOut:
    return RiskOut(
        score=snap.score,
        level=snap.level,
        computed_on=snap.computed_on,
        components=[
            RiskComponentOut(
                key=k, label=risk.LABELS[k], value=snap.components[k]["value"], weight=snap.components[k]["weight"],
                tip=risk.TIPS[k], tip_key=f"risk.tip.{k}",
            )
            for k in risk.WEIGHTS
        ],
    )


async def ensure_risk_snapshot(session: AsyncSession, user_id: uuid.UUID) -> RiskSnapshot | None:
    """Today's snapshot; computed on demand when missing or older than today (spec §5.5)."""
    snap = (
        await session.execute(
            select(RiskSnapshot).where(RiskSnapshot.user_id == user_id).order_by(RiskSnapshot.computed_on.desc()).limit(1)
        )
    ).scalar_one_or_none()
    if snap is not None and snap.computed_on >= today_ist():
        return snap
    inputs = await load_inputs(session, user_id)
    result = risk.compute_risk(inputs)
    if result is None:
        return snap
    snap = await risk.store_snapshot(session, inputs, result)
    await session.commit()
    return snap


async def current_risk(session: AsyncSession, user: User) -> RiskOut:
    snap = await ensure_risk_snapshot(session, user.id)
    if snap is None:
        raise AppError("NOT_FOUND", "Add income and expenses to see your score.")
    return _risk_out(snap)


async def risk_history(session: AsyncSession, user: User, days: int) -> list[RiskHistoryItem]:
    await ensure_risk_snapshot(session, user.id)
    since = today_ist() - timedelta(days=days)
    rows = (
        await session.execute(
            select(RiskSnapshot)
            .where(RiskSnapshot.user_id == user.id, RiskSnapshot.computed_on >= since)
            .order_by(RiskSnapshot.computed_on)
        )
    ).scalars()
    return [RiskHistoryItem(computed_on=r.computed_on, score=r.score, level=r.level) for r in rows]
