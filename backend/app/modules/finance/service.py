"""Transactions and debts (spec §5.5, §7.4). Every query is scoped to the caller's user_id."""

import uuid
from datetime import date, datetime

from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import enums, events
from app.core.errors import AppError
from app.core.pagination import Page, after_cursor, clamp_limit, decode_cursor, encode_cursor
from app.core.redis import redis_client
from app.core.types import month_bounds, today_ist
from app.modules.finance.models import Debt, Transaction
from app.modules.finance.schemas import DebtIn, DebtPatch, TransactionIn, TransactionOut, TransactionPatch
from app.modules.users.models import User

ESSENTIAL = set(enums.ESSENTIAL_CATEGORIES)
CATEGORIES_BY_TYPE = {"income": set(enums.INCOME_CATEGORIES), "expense": set(enums.EXPENSE_CATEGORIES)}


def is_essential(tx_type: str, category: str) -> bool:
    return tx_type == "expense" and category in ESSENTIAL


def _validate_transaction(tx_type: str, category: str, occurred_on: date) -> None:
    errors = []
    if category not in CATEGORIES_BY_TYPE[tx_type]:
        errors.append({"field": "category", "issue": f"not a valid {tx_type} category"})
    if occurred_on > today_ist():
        errors.append({"field": "occurred_on", "issue": "cannot be in the future"})
    if errors:
        raise AppError("VALIDATION_ERROR", details=errors)


async def invalidate_summary(user_id: uuid.UUID) -> None:
    """Drop cached /finance/summary responses for this user (spec §5.11)."""
    try:
        keys = [k async for k in redis_client.scan_iter(f"summary:{user_id}:*")]
        if keys:
            await redis_client.delete(*keys)
    except RedisError:
        pass  # cache entries expire within 60 s anyway


# --- Transactions ------------------------------------------------------------------

async def _get_transaction(session: AsyncSession, user: User, tx_id: uuid.UUID) -> Transaction:
    tx = await session.get(Transaction, tx_id)
    if tx is None or tx.user_id != user.id:
        raise AppError("NOT_FOUND")  # never reveal other users' rows
    return tx


async def list_transactions(
    session: AsyncSession, user: User, month: str | None, tx_type: str | None, limit: int | None, cursor: str | None
) -> Page[TransactionOut]:
    limit = clamp_limit(limit)
    stmt = select(Transaction).where(Transaction.user_id == user.id)
    if month:
        first, last = month_bounds(month)
        stmt = stmt.where(Transaction.occurred_on.between(first, last))
    if tx_type:
        stmt = stmt.where(Transaction.type == tx_type)
    order = (Transaction.occurred_on, Transaction.created_at, Transaction.id)
    if cursor:
        values = decode_cursor(cursor, (date.fromisoformat, datetime.fromisoformat, uuid.UUID))
        stmt = stmt.where(after_cursor(order, values))
    rows = list((await session.execute(stmt.order_by(*(c.desc() for c in order)).limit(limit + 1))).scalars())
    next_cursor = None
    if len(rows) > limit:
        last_row = rows[limit - 1]
        next_cursor = encode_cursor([last_row.occurred_on, last_row.created_at, last_row.id])
        rows = rows[:limit]
    return Page[TransactionOut](items=[TransactionOut.model_validate(r) for r in rows], next_cursor=next_cursor)


async def create_transaction(session: AsyncSession, user: User, body: TransactionIn) -> Transaction:
    _validate_transaction(body.type, body.category, body.occurred_on)
    tx = Transaction(
        user_id=user.id,
        type=body.type,
        amount_inr=body.amount_inr,
        category=body.category,
        is_essential=is_essential(body.type, body.category),
        occurred_on=body.occurred_on,
        note=body.note or None,
        source=body.source,
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    await _transactions_changed(user.id)
    return tx


async def update_transaction(session: AsyncSession, user: User, tx_id: uuid.UUID, body: TransactionPatch) -> Transaction:
    tx = await _get_transaction(session, user, tx_id)
    changes = body.model_dump(exclude_unset=True)
    for field in ("type", "amount_inr", "category", "occurred_on"):
        if field in changes and changes[field] is None:
            raise AppError("VALIDATION_ERROR", details=[{"field": field, "issue": "cannot be null"}])
    new_type = changes.get("type", tx.type)
    new_category = changes.get("category", tx.category)
    _validate_transaction(new_type, new_category, changes.get("occurred_on", tx.occurred_on))
    if "note" in changes:
        changes["note"] = changes["note"] or None  # empty note -> NULL
    for field, value in changes.items():
        setattr(tx, field, value)
    tx.is_essential = is_essential(new_type, new_category)
    await session.commit()
    await session.refresh(tx)
    await _transactions_changed(user.id)
    return tx


async def delete_transaction(session: AsyncSession, user: User, tx_id: uuid.UUID) -> None:
    tx = await _get_transaction(session, user, tx_id)
    await session.delete(tx)
    await session.commit()
    await _transactions_changed(user.id)


async def _transactions_changed(user_id: uuid.UUID) -> None:
    await invalidate_summary(user_id)
    await events.emit(events.TRANSACTIONS_CHANGED, user_id)  # insights + plan refresh (steps 10, 17)


# --- Debts -------------------------------------------------------------------------

async def _get_debt(session: AsyncSession, user: User, debt_id: uuid.UUID) -> Debt:
    debt = await session.get(Debt, debt_id)
    if debt is None or debt.user_id != user.id:
        raise AppError("NOT_FOUND")
    return debt


async def list_debts(session: AsyncSession, user: User) -> list[Debt]:
    stmt = (
        select(Debt)
        .where(Debt.user_id == user.id)
        .order_by((Debt.status == "active").desc(), Debt.principal_outstanding_inr.desc(), Debt.created_at)
    )
    return list((await session.execute(stmt)).scalars())


async def create_debt(session: AsyncSession, user: User, body: DebtIn) -> Debt:
    debt = Debt(user_id=user.id, **body.model_dump())
    session.add(debt)
    await session.commit()
    await session.refresh(debt)
    await _debts_changed(user.id)
    return debt


async def update_debt(session: AsyncSession, user: User, debt_id: uuid.UUID, body: DebtPatch) -> Debt:
    debt = await _get_debt(session, user, debt_id)
    changes = body.model_dump(exclude_unset=True)
    nulls = [f for f, v in changes.items() if v is None and f != "due_day_of_month"]
    if nulls:
        raise AppError("VALIDATION_ERROR", details=[{"field": f, "issue": "cannot be null"} for f in nulls])
    for field, value in changes.items():
        setattr(debt, field, value)
    await session.commit()
    await session.refresh(debt)
    await _debts_changed(user.id)
    return debt


async def delete_debt(session: AsyncSession, user: User, debt_id: uuid.UUID) -> None:
    debt = await _get_debt(session, user, debt_id)
    await session.delete(debt)
    await session.commit()
    await _debts_changed(user.id)


async def _debts_changed(user_id: uuid.UUID) -> None:
    await invalidate_summary(user_id)
    await events.emit(events.DEBTS_CHANGED, user_id)  # risk score refresh (step 10)
