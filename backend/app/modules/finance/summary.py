"""GET /finance/summary — Home dashboard numbers (spec §4.7 S10, §5.5 "Monthly summary", §7.4).

Cached in Redis for 60 s per user+month (spec §5.11); writes to transactions or debts drop it.
"""

import logging
import uuid

from redis.exceptions import RedisError
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.core.types import month_bounds, months_between, today_ist
from app.modules.finance.models import Debt, Transaction
from app.modules.finance.schemas import EmergencyFundSummary, RiskSummary, SummaryOut
from app.modules.goals.models import Goal
from app.modules.notifications.models import Notification
from app.modules.planner.models import EmergencyFundPlan

log = logging.getLogger(__name__)

CACHE_TTL_SEC = 60
PLAN_HORIZON_MONTHS = 12  # spec §5.5: expected_pct uses a fixed 12-month horizon


async def emergency_fund_status(session: AsyncSession, user_id: uuid.UUID) -> EmergencyFundSummary:
    row = (
        await session.execute(
            select(EmergencyFundPlan.started_on, Goal.current_amount_inr, Goal.target_amount_inr)
            .join(Goal, Goal.id == EmergencyFundPlan.goal_id)
            .where(EmergencyFundPlan.user_id == user_id)
        )
    ).first()
    if row is None:
        return EmergencyFundSummary(exists=False, pct=0, expected_pct=0, on_track=None)
    started_on, current, target = row
    pct = min(100, round(100 * float(current) / float(target))) if target else 0
    expected = min(100, round(100 * months_between(started_on, today_ist()) / PLAN_HORIZON_MONTHS))
    return EmergencyFundSummary(exists=True, pct=pct, expected_pct=expected, on_track=pct >= expected)


async def latest_risk(session: AsyncSession, user_id: uuid.UUID) -> RiskSummary | None:
    from app.modules.planner.service import ensure_risk_snapshot  # planner imports finance; avoid a cycle

    snap = await ensure_risk_snapshot(session, user_id)  # computed on demand if missing or stale (§5.5)
    if snap is None:
        return None
    return RiskSummary(score=snap.score, level=snap.level, computed_on=snap.computed_on)


async def compute_summary(session: AsyncSession, user_id: uuid.UUID, month: str | None) -> SummaryOut:
    first, last = month_bounds(month)

    income, expenses = (
        await session.execute(
            select(
                func.coalesce(func.sum(case((Transaction.type == "income", Transaction.amount_inr))), 0),
                func.coalesce(func.sum(case((Transaction.type == "expense", Transaction.amount_inr))), 0),
            ).where(Transaction.user_id == user_id, Transaction.occurred_on.between(first, last))
        )
    ).one()
    has_transactions = (
        await session.execute(select(Transaction.id).where(Transaction.user_id == user_id).limit(1))
    ).first() is not None
    debt_total, debt_count = (
        await session.execute(
            select(func.coalesce(func.sum(Debt.principal_outstanding_inr), 0), func.count(Debt.id)).where(
                Debt.user_id == user_id, Debt.status == "active"
            )
        )
    ).one()
    goals = (
        await session.execute(select(func.count(Goal.id)).where(Goal.user_id == user_id, Goal.status == "active"))
    ).scalar_one()
    unread = (
        await session.execute(
            select(func.count(Notification.id)).where(Notification.user_id == user_id, Notification.read_at.is_(None))
        )
    ).scalar_one()

    return SummaryOut(
        month=f"{first:%Y-%m}",
        income_inr=income,
        expenses_inr=expenses,
        savings_inr=income - expenses,  # spec A14: can be negative
        debt_outstanding_inr=debt_total,
        active_debts_count=debt_count,
        active_goals_count=goals,
        emergency_fund=await emergency_fund_status(session, user_id),
        risk=await latest_risk(session, user_id),
        unread_notifications=unread,
        has_transactions=has_transactions,
    )


async def get_summary(session: AsyncSession, user_id: uuid.UUID, month: str | None) -> SummaryOut:
    key = f"summary:{user_id}:{month_bounds(month)[0]:%Y-%m}"
    try:
        cached = await redis_client.get(key)
        if cached:
            return SummaryOut.model_validate_json(cached)
    except RedisError as exc:
        log.warning("summary cache unavailable", extra={"error": str(exc)})
    summary = await compute_summary(session, user_id, month)
    try:
        await redis_client.set(key, summary.model_dump_json(), ex=CACHE_TTL_SEC)
    except RedisError:
        pass
    return summary
