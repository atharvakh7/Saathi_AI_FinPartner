"""Adaptive monthly budget (spec §5.5 "Adaptive budget").

baseline_income  = 0.8 × median(income series, last 12 months)        (declared min if n < 3)
planning_income  = expected_income_M (lean/normal)  |  baseline + 0.5·(expected − baseline) (surplus)
avg_essential    = mean essential spend, last 3 months with data      (0.5 × planning if none)
needs_limit      = min(max(avg_essential, 0.5·planning), 0.8·planning)
savings_rate     = 0.05 lean / 0.20 normal / 0.35 surplus; +0.10 if a lean month is within the next 3
                   forecast months and the emergency fund is below 100%
savings_target   = round_to_10(planning × savings_rate)
wants_limit      = max(0, planning − needs − savings)
"""

import statistics
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import add_months
from app.modules.planner.data import PlanInputs, round_to, to_money
from app.modules.planner.forecast import forecast_month, income_stats
from app.modules.planner.models import Budget

SAVINGS_RATES = {"lean": 0.05, "normal": 0.20, "surplus": 0.35}
LEAN_BUFFER = 0.10


@dataclass(frozen=True)
class BudgetPlan:
    month: date
    mode: str
    expected_income: float
    planning_income: float
    needs_limit: float
    wants_limit: float
    savings_target: float
    inputs: dict


def compute_budget(inputs: PlanInputs, month: date) -> BudgetPlan:
    n, _, _ = income_stats(inputs)
    fc = forecast_month(inputs, month)
    expected = fc.expected_income

    if n < 3:
        baseline = inputs.declared_min or 0.0
    else:
        last12 = [v for m, v in inputs.income_series if m >= add_months(inputs.current_month, -12)]
        baseline = 0.8 * statistics.median(last12) if last12 else 0.8 * expected

    planning = expected if fc.mode in ("lean", "normal") else baseline + 0.5 * (expected - baseline)
    avg_essential = inputs.avg_essential_3m
    essential_basis = avg_essential if avg_essential is not None else 0.5 * planning
    needs = min(max(essential_basis, 0.5 * planning), 0.8 * planning)

    rate = SAVINGS_RATES[fc.mode]
    upcoming = [forecast_month(inputs, add_months(month, i)) for i in (1, 2, 3)]
    lean_ahead = any(f.mode == "lean" for f in upcoming)
    if lean_ahead and not inputs.ef_complete:
        rate += LEAN_BUFFER
    savings = round_to(planning * rate, 10)
    wants = max(0.0, planning - needs - savings)

    return BudgetPlan(
        month=month,
        mode=fc.mode,
        expected_income=expected,
        planning_income=planning,
        needs_limit=needs,
        wants_limit=wants,
        savings_target=savings,
        inputs={
            "income_months": n,
            "baseline_income": round(baseline, 2),
            "avg_essential": round(avg_essential, 2) if avg_essential is not None else None,
            "savings_rate": round(rate, 2),
            "lean_month_ahead": lean_ahead,
            "emergency_fund_complete": inputs.ef_complete,
            "forecast_confidence": fc.confidence,
            "upcoming_modes": [f.mode for f in upcoming],
        },
    )


async def store_budget(session: AsyncSession, inputs: PlanInputs, plan: BudgetPlan) -> Budget:
    row = {
        "user_id": inputs.user_id,
        "month": plan.month,
        "mode": plan.mode,
        "expected_income_inr": to_money(plan.expected_income),
        "planning_income_inr": to_money(plan.planning_income),
        "needs_limit_inr": to_money(plan.needs_limit),
        "wants_limit_inr": to_money(plan.wants_limit),
        "savings_target_inr": to_money(plan.savings_target),
        "generation_inputs": plan.inputs,
        "generated_at": datetime.now(timezone.utc),
    }
    stmt = insert(Budget).values(row)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "month"], set_={c: stmt.excluded[c] for c in row if c not in ("user_id", "month")}
    ).returning(Budget)
    return (await session.execute(stmt)).scalar_one()

