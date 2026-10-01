"""Financial risk score 0–5 (spec §5.5 "Risk score", §7.4 /risk/*).

e = clamp((avg_expense_3m / avg_income_3m − 0.5) / 0.5)        spending vs income
g = 1 − clamp(ef_current / ef_target)   (1 if no plan)          emergency fund gap
v = clamp(cv)  cv = σ/mean of monthly income if n ≥ 3, else 0.1 / 0.6 / 0.8 by income pattern
d = clamp(Σ min monthly debt payments / avg_income_3m / 0.4)     debt burden
score = round(5 × (0.35e + 0.25g + 0.20v + 0.20d), 1);  low < 2.5 ≤ medium < 3.75 ≤ high
"""

import statistics
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.planner.data import PlanInputs
from app.modules.planner.forecast import income_stats
from app.modules.planner.models import RiskSnapshot

WEIGHTS = {"expense": 0.35, "emergency": 0.25, "volatility": 0.20, "debt": 0.20}
PATTERN_CV = {"fixed_monthly": 0.1, "irregular": 0.6, "seasonal": 0.8}
DEFAULT_CV = 0.6  # pattern unknown: assume irregular
LABELS = {
    "expense": "Spending vs income",
    "emergency": "Emergency fund gap",
    "volatility": "Income ups and downs",
    "debt": "Debt burden",
}
# English fallbacks; the app shows the localized i18n key `risk.tip.<key>` (spec §5.5).
TIPS = {
    "expense": "Try to keep spending below 70% of what you earn.",
    "emergency": "Build an emergency fund worth 3–6 months of expenses.",
    "volatility": "Save more in good months to cover the lean ones.",
    "debt": "Keep loan repayments under 40% of your income; repay costly loans first.",
}


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


@dataclass(frozen=True)
class RiskResult:
    score: float
    level: str
    components: dict  # {key: {"value": float, "weight": float}}


def averages_3m(inputs: PlanInputs) -> tuple[float, float]:
    """(avg income, avg expense) over the last ≤3 completed months with any data; declared fallback."""
    months = inputs.recent_with(lambda t: t.has_data, 3)
    if months:
        return (
            statistics.mean(inputs.totals(m).income for m in months),
            statistics.mean(inputs.totals(m).expense for m in months),
        )
    mid = inputs.declared_mid or 0.0
    return mid, 0.7 * mid


def compute_risk(inputs: PlanInputs) -> RiskResult | None:
    """None when there is nothing to score (no transactions and no declared income)."""
    if not inputs.has_any_data:
        return None
    income, expense = averages_3m(inputs)

    if income > 0:
        e = clamp((expense / income - 0.5) / 0.5)
        d = clamp(inputs.debt_min_payments / income / 0.4)
    else:  # nothing earned: any spending or debt payment is maximum strain
        e = 1.0 if expense > 0 else 0.0
        d = 1.0 if inputs.debt_min_payments > 0 else 0.0

    target = inputs.ef_target
    g = 1.0 if not target else 1.0 - clamp(inputs.ef_current / target)

    n, mean, sigma = income_stats(inputs)
    if n >= 3 and mean:
        v = clamp(sigma / mean)
    else:
        v = PATTERN_CV.get(inputs.income_pattern, DEFAULT_CV)

    values = {"expense": e, "emergency": g, "volatility": v, "debt": d}
    raw = 5 * sum(WEIGHTS[k] * values[k] for k in WEIGHTS)
    # Half-up (2.65 -> 2.7); Python's round() would use banker's rounding.
    score = float(Decimal(str(round(raw, 6))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    level = "low" if score < 2.5 else "medium" if score < 3.75 else "high"
    return RiskResult(
        score=score,
        level=level,
        components={k: {"value": round(values[k], 3), "weight": WEIGHTS[k]} for k in WEIGHTS},
    )


async def store_snapshot(session: AsyncSession, inputs: PlanInputs, result: RiskResult) -> RiskSnapshot:
    row = {
        "user_id": inputs.user_id,
        "computed_on": inputs.today,
        "score": result.score,
        "level": result.level,
        "components": result.components,
    }
    stmt = insert(RiskSnapshot).values(row)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "computed_on"],
        set_={"score": stmt.excluded.score, "level": stmt.excluded.level, "components": stmt.excluded.components},
    ).returning(RiskSnapshot)
    return (await session.execute(stmt)).scalar_one()
