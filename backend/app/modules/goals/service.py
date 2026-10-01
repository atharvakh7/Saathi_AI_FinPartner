"""Goals and contributions (spec §4.7 S17–S19, §7.4). Every query is scoped to the caller."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import events
from app.core.errors import AppError
from app.core.types import today_ist
from app.modules.finance.service import invalidate_summary
from app.modules.goals.models import Goal, GoalContribution, GoalTemplate
from app.modules.goals.projection import monthly_rates, project
from app.modules.goals.schemas import (
    ContributionIn,
    ContributionOut,
    GoalDetailOut,
    GoalIn,
    GoalOut,
    GoalPatch,
    GoalTemplateOut,
)
from app.modules.planner.models import EmergencyFundPlan
from app.modules.users.models import User

# S17 has two tabs: "Active" shows active and paused goals; "Completed" shows completed ones.
STATUS_FILTERS = {
    "active": ("active", "paused"),
    "completed": ("completed",),
    "all": ("active", "paused", "completed", "cancelled"),
}
CONTRIBUTIONS_SHOWN = 50
_EF_CONFLICT = "You already have an emergency fund goal. Add money to it instead."


def _now() -> datetime:
    return datetime.now(timezone.utc)


def to_out(goal: Goal, rate: Decimal) -> GoalOut:
    pct = min(100, int(100 * goal.current_amount_inr / goal.target_amount_inr)) if goal.target_amount_inr else 0
    return GoalOut(
        id=goal.id,
        title=goal.title,
        category=goal.category,
        target_amount_inr=goal.target_amount_inr,
        current_amount_inr=goal.current_amount_inr,
        progress_pct=pct,
        target_date=goal.target_date,
        status=goal.status,
        projection=project(goal, rate),
    )


def sync_completion(goal: Goal) -> None:
    """Reaching the target completes a goal; dropping below it reopens a completed one."""
    if goal.current_amount_inr >= goal.target_amount_inr:
        if goal.status in ("active", "paused"):
            goal.status = "completed"
            goal.completed_at = _now()
    elif goal.status == "completed":
        goal.status = "active"
        goal.completed_at = None


def _validate_target_date(target_date) -> None:
    if target_date is not None and target_date <= today_ist():
        raise AppError("VALIDATION_ERROR", details=[{"field": "target_date", "issue": "must be in the future"}])


async def _changed(user_id: uuid.UUID) -> None:
    await invalidate_summary(user_id)  # Home shows goal count and emergency fund %
    await events.emit(events.GOALS_CHANGED, user_id)


async def _commit_or_conflict(session: AsyncSession) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if "uq_goals_one_emergency_fund" in str(exc.orig):
            raise AppError("CONFLICT", _EF_CONFLICT) from exc
        raise


async def get_goal(session: AsyncSession, user: User, goal_id: uuid.UUID, for_update: bool = False) -> Goal:
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id)
    if for_update:
        stmt = stmt.with_for_update()
    goal = (await session.execute(stmt)).scalar_one_or_none()
    if goal is None:
        raise AppError("NOT_FOUND")
    return goal


async def goal_out(session: AsyncSession, goal: Goal) -> GoalOut:
    rates = await monthly_rates(session, [goal.id])
    return to_out(goal, rates[goal.id])


# --- Queries -----------------------------------------------------------------------

async def list_templates(session: AsyncSession) -> list[GoalTemplateOut]:
    rows = (await session.execute(select(GoalTemplate).order_by(GoalTemplate.sort_order))).scalars()
    return [
        GoalTemplateOut(slug=t.slug, title=t.title_en, category=t.category, default_target_inr=t.default_target_inr)
        for t in rows
    ]


async def list_goals(session: AsyncSession, user: User, status: str) -> list[GoalOut]:
    stmt = (
        select(Goal)
        .where(Goal.user_id == user.id, Goal.status.in_(STATUS_FILTERS[status]))
        .order_by((Goal.status == "paused").asc(), Goal.target_date.asc().nulls_last(), Goal.created_at)
    )
    goals = list((await session.execute(stmt)).scalars())
    rates = await monthly_rates(session, [g.id for g in goals])
    return [to_out(g, rates[g.id]) for g in goals]


async def goal_detail(session: AsyncSession, user: User, goal_id: uuid.UUID) -> GoalDetailOut:
    goal = await get_goal(session, user, goal_id)
    contributions = (
        await session.execute(
            select(GoalContribution)
            .where(GoalContribution.goal_id == goal.id)
            .order_by(GoalContribution.contributed_on.desc(), GoalContribution.created_at.desc())
            .limit(CONTRIBUTIONS_SHOWN)
        )
    ).scalars()
    base = await goal_out(session, goal)
    return GoalDetailOut(**base.model_dump(), contributions=[ContributionOut.model_validate(c) for c in contributions])


# --- Commands ----------------------------------------------------------------------

async def create_goal(session: AsyncSession, user: User, body: GoalIn) -> GoalOut:
    _validate_target_date(body.target_date)
    goal = Goal(user_id=user.id, **body.model_dump())
    sync_completion(goal)
    session.add(goal)
    await _commit_or_conflict(session)
    await session.refresh(goal)
    await _changed(user.id)
    return await goal_out(session, goal)


async def update_goal(session: AsyncSession, user: User, goal_id: uuid.UUID, body: GoalPatch) -> GoalOut:
    goal = await get_goal(session, user, goal_id, for_update=True)
    changes = body.model_dump(exclude_unset=True)
    nulls = [f for f in ("title", "target_amount_inr", "status") if f in changes and changes[f] is None]
    if nulls:
        raise AppError("VALIDATION_ERROR", details=[{"field": f, "issue": "cannot be null"} for f in nulls])
    if "target_date" in changes:
        _validate_target_date(changes["target_date"])

    new_status = changes.pop("status", None)
    for field, value in changes.items():
        setattr(goal, field, value)
    if new_status is not None and new_status != goal.status:
        if goal.status == "cancelled":
            raise AppError("CONFLICT", "This goal was cancelled. Create a new goal instead.")
        if goal.status == "completed" and new_status != "cancelled":
            raise AppError("CONFLICT", "This goal is already complete. Raise the target to keep saving.")
        goal.status = new_status
    sync_completion(goal)  # e.g. lowering the target below the saved amount completes it
    await _commit_or_conflict(session)
    await session.refresh(goal)
    await _changed(user.id)
    return await goal_out(session, goal)


async def delete_goal(session: AsyncSession, user: User, goal_id: uuid.UUID) -> None:
    goal = await get_goal(session, user, goal_id)
    linked = (
        await session.execute(select(EmergencyFundPlan.id).where(EmergencyFundPlan.goal_id == goal.id))
    ).first()
    if linked:
        raise AppError("CONFLICT", "Emergency fund goal cannot be deleted; pause it instead")
    await session.delete(goal)
    await session.commit()
    await _changed(user.id)


async def add_contribution(session: AsyncSession, user: User, goal_id: uuid.UUID, body: ContributionIn) -> GoalOut:
    if body.amount_inr == 0:
        raise AppError("VALIDATION_ERROR", details=[{"field": "amount_inr", "issue": "must not be 0"}])
    contributed_on = body.contributed_on or today_ist()
    if contributed_on > today_ist():
        raise AppError("VALIDATION_ERROR", details=[{"field": "contributed_on", "issue": "cannot be in the future"}])

    goal = await get_goal(session, user, goal_id, for_update=True)  # serialize concurrent taps
    if goal.status == "cancelled":
        raise AppError("CONFLICT", "This goal was cancelled.")
    new_amount = goal.current_amount_inr + body.amount_inr
    if new_amount < 0:
        raise AppError(
            "VALIDATION_ERROR",
            "You can't withdraw more than you have saved in this goal.",
            details=[{"field": "amount_inr", "issue": f"withdrawal exceeds saved amount ({goal.current_amount_inr})"}],
        )
    session.add(GoalContribution(
        goal_id=goal.id, user_id=user.id, amount_inr=body.amount_inr, contributed_on=contributed_on,
        note=body.note or None,
    ))
    goal.current_amount_inr = new_amount  # same transaction as the contribution row (spec §6.1)
    sync_completion(goal)
    await session.commit()
    await session.refresh(goal)
    await _changed(user.id)
    return await goal_out(session, goal)
