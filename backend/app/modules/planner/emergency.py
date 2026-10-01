"""Emergency fund plan (spec §5.5 "Emergency fund", §7.4 /plan/emergency-fund).

target_months       = 6 for irregular/seasonal income or farmer/gig/senior, else 3 (user may override)
monthly_essential   = avg essential spend, last 3 months (else 0.5 × declared mid income)
target_amount       = target_months × monthly_essential, rounded to the nearest ₹100
suggested_monthly   = min(this month's savings target, ceil_to_10((target − current) / 12))   (0 if done)
estimated_completion = today + ceil((target − current) / suggested) months                  (null if 0)
"""

import math
from dataclasses import dataclass
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.goals.models import Goal
from app.modules.goals.projection import add_months_keep_day
from app.modules.goals.service import sync_completion
from app.modules.planner.data import PlanInputs, ceil_to, round_to, to_money
from app.modules.planner.models import EmergencyFundPlan

LONG_BUFFER_PATTERNS = {"irregular", "seasonal"}
LONG_BUFFER_OCCUPATIONS = {"farmer", "gig_worker", "senior_citizen"}


@dataclass(frozen=True)
class EmergencyFigures:
    exists: bool
    target_months: int
    monthly_essential: float
    target_amount: float
    current_amount: float
    suggested_monthly: float
    estimated_completion: date | None
    goal_id: object | None

    @property
    def pct(self) -> int:
        return min(100, int(100 * self.current_amount / self.target_amount)) if self.target_amount else 0


def default_target_months(inputs: PlanInputs) -> int:
    if inputs.income_pattern in LONG_BUFFER_PATTERNS or inputs.occupation_type in LONG_BUFFER_OCCUPATIONS:
        return 6
    return 3


def monthly_essential(inputs: PlanInputs) -> float:
    avg = inputs.avg_essential_3m
    if avg is not None:
        return avg
    return 0.5 * (inputs.declared_mid or 0.0)


def compute(inputs: PlanInputs, savings_target: float, target_months: int | None = None) -> EmergencyFigures:
    plan = inputs.ef_plan
    months = target_months or (plan.target_months if plan else default_target_months(inputs))
    essential = monthly_essential(inputs)
    target = float(round_to(months * essential, 100))
    current = inputs.ef_current
    remaining = max(0.0, target - current)
    suggested = 0.0 if remaining == 0 else float(min(savings_target, ceil_to(remaining / 12, 10)))
    completion = (
        add_months_keep_day(inputs.today, math.ceil(remaining / suggested)) if suggested > 0 and remaining > 0 else None
    )
    return EmergencyFigures(
        exists=plan is not None,
        target_months=months,
        monthly_essential=essential,
        target_amount=target,
        current_amount=current,
        suggested_monthly=suggested,
        estimated_completion=inputs.today if remaining == 0 and target > 0 else completion,
        goal_id=plan.goal_id if plan else (inputs.ef_goal.id if inputs.ef_goal else None),
    )


async def upsert_plan(
    session: AsyncSession, inputs: PlanInputs, figures: EmergencyFigures, create: bool
) -> EmergencyFundPlan | None:
    """Writes the plan and syncs its goal's target. Creates goal + plan only when `create`."""
    plan = inputs.ef_plan
    if plan is None and not create:
        return None
    if figures.target_amount <= 0:
        raise AppError(
            "VALIDATION_ERROR",
            "Add your income or a few expenses first, so Saathi can size your emergency fund.",
            details=[{"field": "target_months", "issue": "no income or expense data to size the fund"}],
        )

    goal = inputs.ef_goal
    if goal is None:
        goal = Goal(user_id=inputs.user_id, title="Emergency Fund", category="emergency_fund",
                    target_amount_inr=to_money(figures.target_amount))
        session.add(goal)
        try:
            await session.flush()
        except IntegrityError as exc:  # another request created one at the same time
            raise AppError("CONFLICT", "An emergency fund goal already exists.") from exc
        inputs.ef_goal = goal
    goal.target_amount_inr = to_money(figures.target_amount)
    sync_completion(goal)

    if plan is None:
        plan = EmergencyFundPlan(user_id=inputs.user_id, goal_id=goal.id, started_on=inputs.today,
                                 target_months=figures.target_months,
                                 monthly_essential_expense_inr=to_money(figures.monthly_essential),
                                 target_amount_inr=to_money(figures.target_amount),
                                 suggested_monthly_contribution_inr=to_money(figures.suggested_monthly))
        session.add(plan)
        inputs.ef_plan = plan
    else:
        plan.target_months = figures.target_months
        plan.monthly_essential_expense_inr = to_money(figures.monthly_essential)
        plan.target_amount_inr = to_money(figures.target_amount)
        plan.suggested_monthly_contribution_inr = to_money(figures.suggested_monthly)
    await session.flush()
    return plan
