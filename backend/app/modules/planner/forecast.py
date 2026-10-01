"""Cash-flow forecast (spec §5.5 "Forecast").

For each target month m:
  n < 3 income months:  expected = declared mid, lower/upper = declared min/max, confidence low
  else:                 w = 0 / 0.5 / 0.75 for 0 / 1 / ≥2 past samples of the same calendar month
                        expected = w·mean(samples) + (1−w)·overall_mean;  lower/upper = expected ∓ σ
                        confidence = medium if n < 12 else high
  expected_expense = mean expenses of the last ≤6 months with data (else 0.7 × declared mid)
  mode = lean if expected < 0.7·mean_income, surplus if > 1.3·mean_income, else normal
"""

import statistics
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import add_months
from app.modules.planner.data import PlanInputs, to_money
from app.modules.planner.models import CashflowForecast

FORECAST_MONTHS = 6
LEAN_RATIO, SURPLUS_RATIO = 0.7, 1.3


@dataclass(frozen=True)
class MonthForecast:
    month: date
    expected_income: float
    lower_income: float
    upper_income: float
    expected_expense: float
    mode: str
    confidence: str

    @property
    def expected_net(self) -> float:
        return self.expected_income - self.expected_expense


def income_stats(inputs: PlanInputs) -> tuple[int, float | None, float]:
    """(n, overall_mean, population σ) of the income series; mean is None when n == 0."""
    values = [v for _, v in inputs.income_series]
    if not values:
        return 0, None, 0.0
    return len(values), statistics.mean(values), statistics.pstdev(values)


def mean_income(inputs: PlanInputs) -> float:
    """§5.5 step 6: overall mean, or the declared mid when there are fewer than 3 income months."""
    n, overall, _ = income_stats(inputs)
    if n < 3:
        return inputs.declared_mid or 0.0
    return overall


def expected_expense(inputs: PlanInputs) -> float:
    months = inputs.recent_with(lambda t: t.expense_count > 0, 6)
    if months:
        return statistics.mean(inputs.totals(m).expense for m in months)
    return 0.7 * (inputs.declared_mid or 0.0)


def classify(expected: float, mean: float) -> str:
    if mean <= 0:
        return "normal"
    if expected < LEAN_RATIO * mean:
        return "lean"
    if expected > SURPLUS_RATIO * mean:
        return "surplus"
    return "normal"


def forecast_month(inputs: PlanInputs, month: date) -> MonthForecast:
    n, overall, sigma = income_stats(inputs)
    expense = expected_expense(inputs)
    if n < 3:
        mid = inputs.declared_mid or 0.0
        lo = inputs.declared_min if inputs.declared_min is not None else mid
        hi = inputs.declared_max if inputs.declared_max is not None else mid
        return MonthForecast(month, mid, lo, hi, expense, classify(mid, mid), "low")

    samples = [v for m, v in inputs.income_series if m.month == month.month]
    w = 0.0 if not samples else 0.5 if len(samples) == 1 else 0.75
    expected = w * (statistics.mean(samples) if samples else 0.0) + (1 - w) * overall
    return MonthForecast(
        month=month,
        expected_income=expected,
        lower_income=max(0.0, expected - sigma),
        upper_income=expected + sigma,
        expected_expense=expense,
        mode=classify(expected, overall),
        confidence="medium" if n < 12 else "high",
    )


def forecast(inputs: PlanInputs, months: int = FORECAST_MONTHS) -> list[MonthForecast]:
    """Next `months` calendar months, starting next month (spec §5.5)."""
    return [forecast_month(inputs, add_months(inputs.current_month, i)) for i in range(1, months + 1)]


async def store_forecast(session: AsyncSession, inputs: PlanInputs, items: list[MonthForecast]) -> None:
    now = datetime.now(timezone.utc)
    rows = [
        {
            "user_id": inputs.user_id,
            "month": f.month,
            "expected_income_inr": to_money(f.expected_income),
            "lower_income_inr": to_money(f.lower_income),
            "upper_income_inr": to_money(f.upper_income),
            "expected_expense_inr": to_money(f.expected_expense),
            "expected_net_inr": to_money(f.expected_net),
            "mode": f.mode,
            "confidence": f.confidence,
            "generated_at": now,
        }
        for f in items
    ]
    stmt = insert(CashflowForecast).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "month"],
        set_={c: stmt.excluded[c] for c in rows[0] if c not in ("user_id", "month")},
    )
    await session.execute(stmt)
