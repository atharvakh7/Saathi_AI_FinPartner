"""Goal projection (spec §5.5 "Goal projection").

monthly_rate = average net contributions over the last 3 full calendar months (0 if none)
projected_completion = today + ceil((target - current) / monthly_rate) months   (null if rate <= 0)
on_track = projected_completion <= target_date                                  (null if no target_date)
"""

import calendar
import math
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import add_months, month_start, today_ist
from app.modules.goals.models import Goal, GoalContribution
from app.modules.goals.schemas import Projection

RATE_WINDOW_MONTHS = 3


def add_months_keep_day(d: date, months: int) -> date:
    """Same day-of-month `months` later, clamped to the month's last day (Jan 31 + 1 -> Feb 28/29)."""
    first = add_months(d, months)
    return first.replace(day=min(d.day, calendar.monthrange(first.year, first.month)[1]))


def rate_window(today: date | None = None) -> tuple[date, date]:
    """[first day 3 months ago, first day of this month) — the last 3 *full* months."""
    this_month = month_start(today or today_ist())
    return add_months(this_month, -RATE_WINDOW_MONTHS), this_month


async def monthly_rates(session: AsyncSession, goal_ids: list[uuid.UUID]) -> dict[uuid.UUID, Decimal]:
    if not goal_ids:
        return {}
    start, end = rate_window()
    rows = await session.execute(
        select(GoalContribution.goal_id, func.coalesce(func.sum(GoalContribution.amount_inr), 0))
        .where(
            GoalContribution.goal_id.in_(goal_ids),
            GoalContribution.contributed_on >= start,
            GoalContribution.contributed_on < end,
        )
        .group_by(GoalContribution.goal_id)
    )
    totals = dict(rows.all())
    return {gid: (Decimal(totals.get(gid, 0)) / RATE_WINDOW_MONTHS).quantize(Decimal("0.01")) for gid in goal_ids}


def project(goal: Goal, monthly_rate: Decimal, today: date | None = None) -> Projection:
    today = today or today_ist()
    remaining = goal.target_amount_inr - goal.current_amount_inr
    if remaining <= 0:
        done = goal.completed_at.date() if goal.completed_at else today
        projected = done
    elif monthly_rate > 0:
        projected = add_months_keep_day(today, math.ceil(remaining / monthly_rate))
    else:
        projected = None
    on_track = None
    if goal.target_date is not None:
        on_track = projected is not None and projected <= goal.target_date
    return Projection(monthly_rate_inr=monthly_rate, projected_completion=projected, on_track=on_track)


def required_monthly(goal: Goal, today: date | None = None) -> Decimal | None:
    """Monthly amount needed to finish by target_date (used by insight I06 in step 17)."""
    today = today or today_ist()
    if goal.target_date is None or goal.target_date <= today:
        return None
    months = max(1, (goal.target_date.year - today.year) * 12 + goal.target_date.month - today.month)
    remaining = max(Decimal(0), goal.target_amount_inr - goal.current_amount_inr)
    return (remaining / months).quantize(Decimal("0.01"))
