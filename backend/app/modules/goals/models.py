"""goals, goal_contributions, goal_templates (spec §6.1)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, SmallInteger, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core import enums
from app.core.db import Base, CreatedAt, Timestamps, UUIDPk, check_in, check_range


class Goal(UUIDPk, Timestamps, Base):
    __tablename__ = "goals"
    __table_args__ = (
        check_in("category", enums.GOAL_CATEGORIES),
        CheckConstraint("target_amount_inr > 0", name="target_amount_inr_positive"),
        check_range("current_amount_inr", 0),
        check_in("status", enums.GOAL_STATUSES),
        Index("ix_goals_user_status", "user_id", "status"),
        # At most one active/paused emergency-fund goal per user.
        Index(
            "uq_goals_one_emergency_fund",
            "user_id",
            unique=True,
            postgresql_where=text("category = 'emergency_fund' AND status IN ('active', 'paused')"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    target_amount_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    current_amount_inr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0"), default=0
    )
    target_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default="active", default="active")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GoalContribution(UUIDPk, CreatedAt, Base):
    __tablename__ = "goal_contributions"
    __table_args__ = (CheckConstraint("amount_inr <> 0", name="amount_inr_nonzero"),)

    goal_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)  # negative = withdrawal
    contributed_on: Mapped[date] = mapped_column(Date, nullable=False, server_default=text("CURRENT_DATE"))
    note: Mapped[str | None] = mapped_column(String(200))


Index("ix_goal_contributions_goal_date", GoalContribution.goal_id, GoalContribution.contributed_on.desc())


class GoalTemplate(Base):
    __tablename__ = "goal_templates"
    __table_args__ = (check_in("category", enums.GOAL_CATEGORIES),)

    slug: Mapped[str] = mapped_column(String(20), primary_key=True)
    title_en: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    default_target_inr: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
