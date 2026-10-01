"""transactions, debts (spec §6.1)."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, Numeric, SmallInteger, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core import enums
from app.core.db import Base, Timestamps, UUIDPk, check_in, check_range, sql_list


class Transaction(UUIDPk, Timestamps, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        check_in("type", enums.TRANSACTION_TYPES),
        CheckConstraint("amount_inr > 0", name="amount_inr_positive"),
        # Category must belong to the list for its type (spec §6.1 enums).
        CheckConstraint(
            f"(type = 'income' AND category IN ({sql_list(enums.INCOME_CATEGORIES)})) OR "
            f"(type = 'expense' AND category IN ({sql_list(enums.EXPENSE_CATEGORIES)}))",
            name="category_matches_type",
        ),
        CheckConstraint("type = 'expense' OR is_essential = false", name="income_not_essential"),
        check_in("source", enums.TRANSACTION_SOURCES),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(7), nullable=False)
    amount_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(25), nullable=False)
    is_essential: Mapped[bool] = mapped_column(Boolean, nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(8), nullable=False, server_default="manual", default="manual")


Index("ix_transactions_user_occurred", Transaction.user_id, Transaction.occurred_on.desc())
Index("ix_transactions_user_type_occurred", Transaction.user_id, Transaction.type, Transaction.occurred_on)


class Debt(UUIDPk, Timestamps, Base):
    __tablename__ = "debts"
    __table_args__ = (
        check_in("debt_type", enums.DEBT_TYPES),
        check_range("principal_outstanding_inr", 0),
        check_range("interest_rate_pct", 0, 120),
        check_range("min_monthly_payment_inr", 0),
        check_range("due_day_of_month", 1, 31),
        check_in("status", enums.DEBT_STATUSES),
        Index("ix_debts_user_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lender_name: Mapped[str] = mapped_column(String(80), nullable=False)
    debt_type: Mapped[str] = mapped_column(String(20), nullable=False)
    principal_outstanding_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    interest_rate_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default=text("0"), default=0)
    min_monthly_payment_inr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0"), default=0
    )
    due_day_of_month: Mapped[int | None] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(8), nullable=False, server_default="active", default="active")
