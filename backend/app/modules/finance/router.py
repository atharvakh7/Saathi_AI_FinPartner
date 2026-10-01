"""/finance/summary, /transactions/*, /debts/* (spec §7.2, §7.4)."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.pagination import Page
from app.core.rate_limit import rate_limit
from app.core.security import get_current_user
from app.core.types import MonthStr
from app.modules.finance import service
from app.modules.finance.parse import parse_transaction_text
from app.modules.finance.schemas import (
    DebtIn,
    DebtOut,
    DebtPatch,
    ParseIn,
    ParseOut,
    SummaryOut,
    TransactionIn,
    TransactionOut,
    TransactionPatch,
)
from app.modules.finance.summary import get_summary
from app.modules.users.models import User

router = APIRouter(tags=["finance"])


@router.get("/finance/summary", response_model=SummaryOut)
async def finance_summary(
    month: MonthStr | None = None, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    return await get_summary(session, user.id, month)


# --- Transactions ------------------------------------------------------------------

@router.get("/transactions", response_model=Page[TransactionOut])
async def list_transactions(
    month: MonthStr | None = None,
    type: Literal["income", "expense"] | None = None,
    limit: int | None = Query(default=None),
    cursor: str | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await service.list_transactions(session, user, month, type, limit, cursor)


@router.post("/transactions", response_model=TransactionOut, status_code=201)
async def create_transaction(
    body: TransactionIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    return await service.create_transaction(session, user, body)


@router.post(
    "/transactions/parse", response_model=ParseOut, dependencies=[Depends(rate_limit("transactions_parse", 20, 60))]
)
async def parse_transaction(body: ParseIn, user: User = Depends(get_current_user)):
    return await parse_transaction_text(body.text)


@router.patch("/transactions/{tx_id}", response_model=TransactionOut)
async def update_transaction(
    tx_id: uuid.UUID, body: TransactionPatch, user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await service.update_transaction(session, user, tx_id, body)


@router.delete("/transactions/{tx_id}", status_code=204)
async def delete_transaction(
    tx_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> Response:
    await service.delete_transaction(session, user, tx_id)
    return Response(status_code=204)


# --- Debts -------------------------------------------------------------------------

@router.get("/debts", response_model=list[DebtOut])
async def list_debts(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.list_debts(session, user)


@router.post("/debts", response_model=DebtOut, status_code=201)
async def create_debt(body: DebtIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.create_debt(session, user, body)


@router.patch("/debts/{debt_id}", response_model=DebtOut)
async def update_debt(
    debt_id: uuid.UUID, body: DebtPatch, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    return await service.update_debt(session, user, debt_id, body)


@router.delete("/debts/{debt_id}", status_code=204)
async def delete_debt(
    debt_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> Response:
    await service.delete_debt(session, user, debt_id)
    return Response(status_code=204)
