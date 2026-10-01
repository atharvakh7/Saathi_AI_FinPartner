"""Planner and risk responses (spec §4.7 S12/S20/S21, §7.4 /plan/*, /risk/*)."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.types import Money

Mode = Literal["lean", "normal", "surplus"]
Confidence = Literal["low", "medium", "high"]


class PatternOut(BaseModel):
    label: Literal["steady", "ups_and_downs", "seasonal"]
    cv: float
    months_of_data: int


class IncomeMonthOut(BaseModel):
    month: str  # YYYY-MM
    income_inr: Money
    is_lean: bool


class ForecastMonthOut(BaseModel):
    month: str
    expected_income_inr: Money
    lower_income_inr: Money
    upper_income_inr: Money
    expected_expense_inr: Money
    expected_net_inr: Money
    mode: Mode
    confidence: Confidence


class BudgetOut(BaseModel):
    month: str
    mode: Mode
    expected_income_inr: Money
    planning_income_inr: Money
    needs_limit_inr: Money
    wants_limit_inr: Money
    savings_target_inr: Money
    spent_needs_inr: Money
    spent_wants_inr: Money
    saved_so_far_inr: Money
    generated_at: datetime


class BudgetRegenerateOut(BaseModel):
    status: Literal["ok"] = "ok"
    budget: BudgetOut


class EmergencyOverviewOut(BaseModel):
    exists: bool
    target_inr: Money
    current_inr: Money
    pct: int


class OverviewOut(BaseModel):
    has_data: bool  # False -> S20 empty state "Tell me about your income"
    pattern: PatternOut
    income_history: list[IncomeMonthOut]
    forecast: list[ForecastMonthOut]
    current_budget: BudgetOut
    emergency_fund: EmergencyOverviewOut
    tight_months: list[str]
    data_confidence: Confidence


class EmergencyFundOut(BaseModel):
    exists: bool
    target_months: int
    monthly_essential_expense_inr: Money
    target_amount_inr: Money
    current_amount_inr: Money
    pct: int
    suggested_monthly_contribution_inr: Money
    estimated_completion_date: date | None
    goal_id: uuid.UUID | None


class EmergencyFundIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_months: int = Field(ge=1, le=12)


class RiskComponentOut(BaseModel):
    key: Literal["expense", "emergency", "volatility", "debt"]
    label: str
    value: float
    weight: float
    tip: str
    tip_key: str


class RiskOut(BaseModel):
    score: Money
    level: Literal["low", "medium", "high"]
    computed_on: date
    components: list[RiskComponentOut]


class RiskHistoryItem(BaseModel):
    computed_on: date
    score: Money
    level: Literal["low", "medium", "high"]
