"""emergency_fund_plans, budgets, cashflow_forecasts, risk_snapshots (spec §5.5, §6.1)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core import enums
from app.core.db import Base, CreatedAt, UpdatedAt, UUIDPk, check_in, check_range

_FIRST_OF_MONTH = "EXTRACT(DAY FROM month) = 1"


class EmergencyFundPlan(UUIDPk, CreatedAt, UpdatedAt, Base):
    __tablename__ = "emergency_fund_plans"
    __table_args__ = (check_range("target_months", 1, 12),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    goal_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("goals.id"), nullable=False, unique=True)
    target_months: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    monthly_essential_expense_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    target_amount_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    suggested_monthly_contribution_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    started_on: Mapped[date] = mapped_column(Date, nullable=False, server_default=text("CURRENT_DATE"))


class Budget(UUIDPk, CreatedAt, Base):
    __tablename__ = "budgets"
    __table_args__ = (
        check_in("mode", enums.BUDGET_MODES),
        CheckConstraint(_FIRST_OF_MONTH, name="month_first_day"),
        UniqueConstraint("user_id", "month"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    month: Mapped[date] = mapped_column(Date, nullable=False)  # first day of month
    mode: Mapped[str] = mapped_column(String(8), nullable=False)
    expected_income_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    planning_income_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    needs_limit_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    wants_limit_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    savings_target_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    generation_inputs: Mapped[dict] = mapped_column(JSONB, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CashflowForecast(UUIDPk, CreatedAt, Base):
    __tablename__ = "cashflow_forecasts"
    __table_args__ = (
        check_in("mode", enums.BUDGET_MODES),
        check_in("confidence", enums.FORECAST_CONFIDENCE),
        CheckConstraint(_FIRST_OF_MONTH, name="month_first_day"),
        UniqueConstraint("user_id", "month"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    month: Mapped[date] = mapped_column(Date, nullable=False)
    expected_income_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    lower_income_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    upper_income_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expected_expense_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expected_net_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    mode: Mapped[str] = mapped_column(String(8), nullable=False)
    confidence: Mapped[str] = mapped_column(String(6), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RiskSnapshot(UUIDPk, CreatedAt, Base):
    __tablename__ = "risk_snapshots"
    __table_args__ = (
        check_range("score", 0, 5),
        check_in("level", enums.RISK_LEVELS),
        UniqueConstraint("user_id", "computed_on"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    computed_on: Mapped[date] = mapped_column(Date, nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False)
    level: Mapped[str] = mapped_column(String(6), nullable=False)
    components: Mapped[dict] = mapped_column(JSONB, nullable=False)
