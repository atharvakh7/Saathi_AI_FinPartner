"""Inputs for the planner formulas (spec §5.5), loaded once per computation.

Months are calendar months in IST, keyed by their first day. "Completed" months exclude the
current month: a half-finished month would look like a lean month to every formula.
"""

import math
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import add_months, month_start, today_ist
from app.modules.finance.models import Debt, Transaction
from app.modules.goals.models import Goal
from app.modules.planner.models import EmergencyFundPlan
from app.modules.users.models import UserProfile

HISTORY_MONTHS = 24


@dataclass
class MonthTotals:
    income: float = 0.0
    expense: float = 0.0
    essential: float = 0.0
    income_count: int = 0
    expense_count: int = 0

    @property
    def nonessential(self) -> float:
        return self.expense - self.essential

    @property
    def has_data(self) -> bool:
        return self.income_count > 0 or self.expense_count > 0


@dataclass
class PlanInputs:
    user_id: uuid.UUID
    today: date
    current_month: date
    income_pattern: str | None
    occupation_type: str | None
    declared_min: float | None
    declared_max: float | None
    months: dict[date, MonthTotals] = field(default_factory=dict)  # 24 completed months + current month
    debt_min_payments: float = 0.0
    ef_plan: EmergencyFundPlan | None = None
    ef_goal: Goal | None = None  # plan's goal, or an unlinked active/paused emergency_fund goal

    # --- declared income -----------------------------------------------------------
    @property
    def declared_mid(self) -> float | None:
        values = [v for v in (self.declared_min, self.declared_max) if v is not None]
        return sum(values) / len(values) if values else None

    @property
    def has_any_data(self) -> bool:
        return self.declared_mid is not None or any(m.has_data for m in self.months.values())

    # --- month helpers --------------------------------------------------------------
    def completed_months(self, back: int = HISTORY_MONTHS) -> list[date]:
        """Completed months, newest first."""
        return [add_months(self.current_month, -i) for i in range(1, back + 1)]

    def totals(self, month: date) -> MonthTotals:
        return self.months.get(month, MonthTotals())

    @property
    def income_series(self) -> list[tuple[date, float]]:
        """§5.5 forecast step 1: last 24 completed months containing ≥1 income transaction, oldest first."""
        return [(m, self.totals(m).income) for m in reversed(self.completed_months()) if self.totals(m).income_count]

    def recent_with(self, predicate, limit: int) -> list[date]:
        """Most recent completed months (≤ limit) whose totals satisfy predicate."""
        return [m for m in self.completed_months() if predicate(self.totals(m))][:limit]

    # --- derived figures used by several formulas -----------------------------------
    @property
    def avg_essential_3m(self) -> float | None:
        months = self.recent_with(lambda t: t.essential > 0, 3)
        return statistics.mean(self.totals(m).essential for m in months) if months else None

    @property
    def ef_current(self) -> float:
        return float(self.ef_goal.current_amount_inr) if self.ef_goal else 0.0

    @property
    def ef_target(self) -> float | None:
        if self.ef_plan is not None:
            return float(self.ef_plan.target_amount_inr)
        return float(self.ef_goal.target_amount_inr) if self.ef_goal else None

    @property
    def ef_complete(self) -> bool:
        target = self.ef_target
        return bool(target) and self.ef_current >= target


def round_to(value: float, step: int) -> int:
    """Round half up to the nearest `step` (₹10, ₹100)."""
    return int(math.floor(value / step + 0.5) * step)


def ceil_to(value: float, step: int) -> int:
    return int(math.ceil(value / step) * step)


def to_money(value: float) -> Decimal:
    return Decimal(str(round(value, 2)))


async def load_inputs(session: AsyncSession, user_id: uuid.UUID) -> PlanInputs:
    today = today_ist()
    current = month_start(today)
    profile = await session.get(UserProfile, user_id)
    inputs = PlanInputs(
        user_id=user_id,
        today=today,
        current_month=current,
        income_pattern=profile.income_pattern if profile else None,
        occupation_type=profile.occupation_type if profile else None,
        declared_min=float(profile.declared_monthly_income_min_inr) if profile and profile.declared_monthly_income_min_inr is not None else None,
        declared_max=float(profile.declared_monthly_income_max_inr) if profile and profile.declared_monthly_income_max_inr is not None else None,
    )

    month_col = func.date_trunc("month", Transaction.occurred_on).label("month")
    is_income = Transaction.type == "income"
    rows = await session.execute(
        select(
            month_col,
            func.coalesce(func.sum(case((is_income, Transaction.amount_inr))), 0),
            func.coalesce(func.sum(case((~is_income, Transaction.amount_inr))), 0),
            func.coalesce(func.sum(case((Transaction.is_essential, Transaction.amount_inr))), 0),
            func.count(case((is_income, 1))),
            func.count(case((~is_income, 1))),
        )
        .where(Transaction.user_id == user_id, Transaction.occurred_on >= add_months(current, -HISTORY_MONTHS))
        .group_by(month_col)
    )
    for month, income, expense, essential, n_inc, n_exp in rows.all():
        key = month.date() if hasattr(month, "date") else month
        inputs.months[key] = MonthTotals(float(income), float(expense), float(essential), n_inc, n_exp)

    inputs.debt_min_payments = float(
        (
            await session.execute(
                select(func.coalesce(func.sum(Debt.min_monthly_payment_inr), 0)).where(
                    Debt.user_id == user_id, Debt.status == "active"
                )
            )
        ).scalar_one()
    )

    inputs.ef_plan = (
        await session.execute(select(EmergencyFundPlan).where(EmergencyFundPlan.user_id == user_id))
    ).scalar_one_or_none()
    if inputs.ef_plan is not None:
        inputs.ef_goal = await session.get(Goal, inputs.ef_plan.goal_id)
    else:
        inputs.ef_goal = (
            await session.execute(
                select(Goal).where(
                    Goal.user_id == user_id, Goal.category == "emergency_fund", Goal.status.in_(("active", "paused"))
                )
            )
        ).scalar_one_or_none()
    return inputs
