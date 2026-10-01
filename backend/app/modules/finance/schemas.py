"""Finance request/response bodies (spec §4.7 S14–S16, §7.3 TransactionDTO, §7.4 finance)."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core import enums
from app.core.types import Money

TxType = Literal["income", "expense"]
TxCategory = Literal[enums.INCOME_CATEGORIES + enums.EXPENSE_CATEGORIES]  # type: ignore[valid-type]
TxSource = Literal["manual", "voice", "chat"]
DebtType = Literal[enums.DEBT_TYPES]  # type: ignore[valid-type]
Note = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
# S15: > 0, at most ₹1,00,00,000, at most 2 decimals.
TxAmount = Annotated[Decimal, Field(gt=0, le=10_000_000, max_digits=10, decimal_places=2)]


# --- Transactions ------------------------------------------------------------------

class TransactionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: TxType
    amount_inr: TxAmount
    category: TxCategory
    occurred_on: date
    note: Note | None = None
    source: TxSource = "manual"


class TransactionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: TxType | None = None
    amount_inr: TxAmount | None = None
    category: TxCategory | None = None
    occurred_on: date | None = None
    note: Note | None = None


class TransactionOut(BaseModel):
    """TransactionDTO."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: TxType
    amount_inr: Money
    category: str
    is_essential: bool
    occurred_on: date
    note: str | None
    source: str
    created_at: datetime


class ParseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    language: Literal["en", "hi", "mr", "ta"] | None = None


class TransactionDraft(BaseModel):
    type: TxType
    amount_inr: Money
    category: str
    occurred_on: date
    note: str | None


class ParseOut(BaseModel):
    draft: TransactionDraft
    confidence: float


# --- Debts -------------------------------------------------------------------------

LenderName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
DebtAmount = Annotated[Decimal, Field(ge=0, le=100_000_000, max_digits=12, decimal_places=2)]


class DebtIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lender_name: LenderName
    debt_type: DebtType
    principal_outstanding_inr: Annotated[Decimal, Field(gt=0, le=100_000_000, max_digits=12, decimal_places=2)]
    interest_rate_pct: Annotated[Decimal, Field(ge=0, le=120, max_digits=5, decimal_places=2)] = Decimal(0)
    min_monthly_payment_inr: DebtAmount = Decimal(0)
    due_day_of_month: int | None = Field(default=None, ge=1, le=31)


class DebtPatch(BaseModel):
    """Any subset. principal may drop to 0 when paid off; status 'closed' archives the debt."""

    model_config = ConfigDict(extra="forbid")
    lender_name: LenderName | None = None
    debt_type: DebtType | None = None
    principal_outstanding_inr: DebtAmount | None = None
    interest_rate_pct: Annotated[Decimal, Field(ge=0, le=120, max_digits=5, decimal_places=2)] | None = None
    min_monthly_payment_inr: DebtAmount | None = None
    due_day_of_month: int | None = Field(default=None, ge=1, le=31)
    status: Literal["active", "closed"] | None = None


class DebtOut(BaseModel):
    """DebtDTO."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    lender_name: str
    debt_type: str
    principal_outstanding_inr: Money
    interest_rate_pct: Money
    min_monthly_payment_inr: Money
    due_day_of_month: int | None
    status: str


# --- Summary -----------------------------------------------------------------------

class EmergencyFundSummary(BaseModel):
    exists: bool
    pct: int
    expected_pct: int
    on_track: bool | None


class RiskSummary(BaseModel):
    score: Money
    level: Literal["low", "medium", "high"]
    computed_on: date


class SummaryOut(BaseModel):
    month: str
    income_inr: Money
    expenses_inr: Money
    savings_inr: Money
    debt_outstanding_inr: Money
    active_debts_count: int
    active_goals_count: int
    emergency_fund: EmergencyFundSummary
    risk: RiskSummary | None
    unread_notifications: int
    has_transactions: bool
