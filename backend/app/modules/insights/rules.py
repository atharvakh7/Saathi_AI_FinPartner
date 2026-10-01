"""Insight rules I01–I09 (spec §5.9). Numbers are computed here, never by the LLM.

Each rule returns Candidate(s) with an English title/body plus `payload` (the variables), so the app
can render its own `insight.<code>` strings and the LLM rewrite can be checked against them.

I09 (new eligible schemes) is created from the schemes recompute, not from this daily pass.
"""

import calendar
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import add_months
from app.modules.finance.models import Transaction
from app.modules.finance.summary import emergency_fund_status
from app.modules.goals.models import Goal
from app.modules.goals.projection import monthly_rates, project, required_monthly
from app.modules.planner.data import PlanInputs, load_inputs, round_to
from app.modules.planner.models import Budget, CashflowForecast
from app.modules.schemes.models import Scheme, UserSchemeMatch

EF_MILESTONES = (25, 50, 75, 100)
INSIGHT_TTL = timedelta(days=30)


@dataclass
class Candidate:
    code: str
    type: str
    tone: str
    filter_group: str
    title: str
    body: str
    dedupe_key: str
    cta_route: str | None = None
    payload: dict = field(default_factory=dict)


def _inr(value: float | Decimal) -> str:
    """₹ with Indian grouping, whole rupees."""
    n = str(int(round(float(value))))
    if len(n) <= 3:
        return n
    head, tail = n[:-3], n[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(([head] if head else []) + groups + [tail])


def _ym(d: date) -> str:
    return f"{d:%Y-%m}"


def _same_day_cutoff(month: date, day: int) -> date:
    return month.replace(day=min(day, calendar.monthrange(month.year, month.month)[1]))


# --- I01 food spending up ----------------------------------------------------------

async def i01_food(session: AsyncSession, inputs: PlanInputs) -> Candidate | None:
    today, cur = inputs.today, inputs.current_month
    start = add_months(cur, -3)
    month_col = func.date_trunc("month", Transaction.occurred_on).label("month")
    rows = (await session.execute(
        select(month_col, func.sum(Transaction.amount_inr))
        .where(Transaction.user_id == inputs.user_id, Transaction.type == "expense", Transaction.category == "food",
               Transaction.occurred_on >= start, Transaction.occurred_on <= today,
               extract("day", Transaction.occurred_on) <= today.day)  # prorated: same day-of-month
        .group_by(month_col)
    )).all()
    by_month = {(m.date() if hasattr(m, "date") else m): float(v) for m, v in rows}
    mtd = by_month.get(cur, 0.0)
    prior = [by_month.get(add_months(cur, -i), 0.0) for i in (1, 2, 3)]
    if not any(prior):
        return None
    avg = sum(prior) / 3
    excess = mtd - avg
    if mtd < 1.15 * avg or excess < 500:
        return None
    pct = round((mtd / avg - 1) * 100)
    amt = round_to(excess, 10)
    return Candidate(
        "I01", "spending", "warning", "spending", "Food spending is up",
        f"You spent {pct}% more on food this month. Try cooking at home to save about ₹{_inr(amt)} monthly.",
        f"I01:{_ym(cur)}", "/transactions", {"pct": pct, "amt": amt},
    )


# --- I02 non-essential spending ----------------------------------------------------

def i02_save_more(inputs: PlanInputs) -> Candidate | None:
    months = inputs.recent_with(lambda t: t.expense_count > 0, 3)
    if not months:
        return None
    avg = sum(inputs.totals(m).expense - inputs.totals(m).essential for m in months) / len(months)
    if avg < 800:
        return None
    amt = max(200, round_to(0.25 * avg, 10))
    return Candidate(
        "I02", "savings", "info", "savings", "A chance to save more",
        f"You can save ₹{_inr(amt)} more monthly. Cut unnecessary subscriptions and boost savings.",
        f"I02:{_ym(inputs.current_month)}", "/plan", {"amt": amt},
    )


# --- I03 emergency fund milestones -------------------------------------------------

async def i03_emergency(session: AsyncSession, user_id: uuid.UUID) -> Candidate | None:
    ef = await emergency_fund_status(session, user_id)
    reached = [m for m in EF_MILESTONES if ef.exists and ef.pct >= m]
    if not reached:
        return None
    pct = reached[-1]
    return Candidate(
        "I03", "emergency_fund", "positive", "goals", f"Emergency fund {pct}% done",
        f"Emergency fund goal is {pct}% complete. You're closer to financial safety.",
        f"I03:{pct}", "/plan/emergency-fund", {"pct": pct},
    )


# --- I04 savings grew --------------------------------------------------------------

def i04_savings_up(inputs: PlanInputs) -> Candidate | None:
    if inputs.today.day < 25:
        return None
    this, last = inputs.totals(inputs.current_month), inputs.totals(add_months(inputs.current_month, -1))
    net_this, net_last = this.income - this.expense, last.income - last.expense
    if net_last <= 0 or net_this < 1.10 * net_last:
        return None
    pct = round((net_this / net_last - 1) * 100)
    return Candidate(
        "I04", "savings", "positive", "savings", "Your savings grew!",
        f"Great! Your savings increased by {pct}%.", f"I04:{_ym(inputs.current_month)}", "/plan", {"pct": pct},
    )


# --- I05 lean months ahead ---------------------------------------------------------

async def i05_lean_ahead(session: AsyncSession, inputs: PlanInputs) -> Candidate | None:
    nxt = [add_months(inputs.current_month, 1), add_months(inputs.current_month, 2)]
    lean = list((await session.execute(
        select(CashflowForecast.month).where(CashflowForecast.user_id == inputs.user_id,
                                             CashflowForecast.month.in_(nxt), CashflowForecast.mode == "lean")
        .order_by(CashflowForecast.month)
    )).scalars())
    if not lean:
        return None
    target = (await session.execute(
        select(Budget.savings_target_inr).where(Budget.user_id == inputs.user_id, Budget.month == inputs.current_month)
    )).scalar_one_or_none()
    amt = round_to(float(target or 0) * 0.5, 10)
    months = " and ".join(f"{m:%B}" for m in lean)
    body = f"Money may be tight in {months}. " + (f"Try to save ₹{_inr(amt)} extra now." if amt >= 10
                                                   else "Try to keep a little extra aside now.")
    return Candidate("I05", "savings", "warning", "savings", "Tight months ahead", body,
                     f"I05:{_ym(inputs.current_month)}", "/plan", {"months": [_ym(m) for m in lean], "amt": amt})


# --- I06 goals behind --------------------------------------------------------------

async def i06_goals_behind(session: AsyncSession, inputs: PlanInputs) -> list[Candidate]:
    goals = list((await session.execute(
        select(Goal).where(Goal.user_id == inputs.user_id, Goal.status == "active", Goal.target_date.is_not(None))
    )).scalars())
    rates = await monthly_rates(session, [g.id for g in goals])
    out = []
    for g in goals:
        if project(g, rates.get(g.id, Decimal(0)), inputs.today).on_track is not False:
            continue
        need = required_monthly(g, inputs.today)
        if need is None or need <= 0:
            continue
        amt = int(-(-float(need) // 10) * 10)  # round up to ₹10
        out.append(Candidate(
            "I06", "goal", "warning", "goals", f"'{g.title}' needs a push"[:120],
            f"'{g.title}' is behind. Adding ₹{_inr(amt)} monthly will get you there by {g.target_date:%d %b %Y}.",
            f"I06:{g.id}:{_ym(inputs.current_month)}", f"/goals/{g.id}",
            {"goal_id": str(g.id), "title": g.title, "amt": amt, "date": g.target_date.isoformat()},
        ))
    return out


# --- I07 no recent income ----------------------------------------------------------

async def i07_no_income(session: AsyncSession, inputs: PlanInputs) -> Candidate | None:
    recent = (await session.execute(
        select(func.count(Transaction.id)).where(
            Transaction.user_id == inputs.user_id, Transaction.type == "income",
            Transaction.occurred_on > inputs.today - timedelta(days=30))
    )).scalar_one()
    if recent:
        return None
    return Candidate("I07", "income", "info", "other", "Add your recent income",
                     "Have you earned anything recently? Add it so I can plan better.",
                     f"I07:{_ym(inputs.current_month)}", "/transactions/new")


# --- I08 scheme deadlines ----------------------------------------------------------

async def i08_deadlines(session: AsyncSession, user_id: uuid.UUID, today: date) -> list[Candidate]:
    rows = (await session.execute(
        select(Scheme).join(UserSchemeMatch, UserSchemeMatch.scheme_id == Scheme.id)
        .where(UserSchemeMatch.user_id == user_id, UserSchemeMatch.status.in_(("eligible", "possibly_eligible")),
               Scheme.is_active, Scheme.deadline_on >= today, Scheme.deadline_on <= today + timedelta(days=14))
    )).scalars()
    return [
        Candidate("I08", "scheme", "warning", "other", "Scheme deadline soon",
                  f"Deadline near for {s.name_en}: {s.deadline_on:%d %b %Y}.", f"I08:{s.id}", f"/schemes/{s.id}",
                  {"scheme_id": str(s.id), "scheme": s.name_en, "date": s.deadline_on.isoformat()})
        for s in rows
    ]


# --- I09 new eligible schemes (from schemes.recompute) -----------------------------

def i09_new_schemes(scheme_ids: list) -> Candidate | None:
    if not scheme_ids:
        return None
    ids = sorted(str(i) for i in scheme_ids)
    digest = hashlib.sha256(",".join(ids).encode()).hexdigest()[:16]
    n = len(ids)
    return Candidate("I09", "scheme", "positive", "other", "New schemes for you",
                     f"You may now qualify for {n} new scheme{'s' if n != 1 else ''}.", f"I09:{digest}",
                     "/schemes/results", {"n": n, "scheme_ids": ids})


async def daily_candidates(session: AsyncSession, user_id: uuid.UUID) -> list[Candidate]:
    inputs = await load_inputs(session, user_id)
    found: list[Candidate | None] = [
        await i01_food(session, inputs), i02_save_more(inputs), await i03_emergency(session, user_id),
        i04_savings_up(inputs), await i05_lean_ahead(session, inputs), await i07_no_income(session, inputs),
    ]
    found += await i06_goals_behind(session, inputs)
    found += await i08_deadlines(session, user_id, inputs.today)
    return [c for c in found if c is not None]


def expiry() -> datetime:
    return datetime.now(timezone.utc) + INSIGHT_TTL

