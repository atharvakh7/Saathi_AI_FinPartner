"""users, user_profiles, consents, device_tokens, notification_settings (spec §6.1)."""

import uuid
from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Time,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import enums
from app.core.db import Base, CreatedAt, Timestamps, UpdatedAt, UUIDPk, check_in, check_range


class User(UUIDPk, Timestamps, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(r"phone_e164 ~ '^\+91[6-9][0-9]{9}$'", name="phone_e164_format"),
        check_in("role", enums.ROLES),
        check_in("preferred_language", enums.LANGUAGES),
        check_in("status", enums.USER_STATUSES),
    )

    phone_e164: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False, server_default="user", default="user")
    preferred_language: Mapped[str] = mapped_column(String(2), nullable=False, server_default="en", default="en")
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default="active", default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped["UserProfile | None"] = relationship(back_populates="user", uselist=False, lazy="raise")


class UserProfile(Timestamps, Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        check_range("age_years", 18, 100),
        check_in("gender", enums.GENDERS),
        check_in("state_code", enums.STATE_CODES),
        check_in("area_type", enums.AREA_TYPES),
        check_in("occupation_type", enums.OCCUPATION_TYPES),
        check_in("income_pattern", enums.INCOME_PATTERNS),
        check_range("declared_monthly_income_min_inr", 0),
        CheckConstraint(
            "declared_monthly_income_max_inr >= 0 AND "
            "(declared_monthly_income_min_inr IS NULL OR declared_monthly_income_max_inr >= declared_monthly_income_min_inr)",
            name="declared_monthly_income_max_inr_range",
        ),
        check_range("household_size", 1, 20),
        check_range("dependents_count", 0, 19),
        check_range("annual_household_income_inr", 0),
        check_range("land_holding_hectares", 0, 500),
        check_in("social_category", enums.SOCIAL_CATEGORIES),
        check_range("confidence_score_pct", 0, 100),
        check_in("confidence_level", enums.CONFIDENCE_LEVELS),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(80))
    age_years: Mapped[int | None] = mapped_column(SmallInteger)
    gender: Mapped[str | None] = mapped_column(String(20))
    state_code: Mapped[str | None] = mapped_column(String(2))
    district: Mapped[str | None] = mapped_column(String(60))
    area_type: Mapped[str | None] = mapped_column(String(10))
    occupation_type: Mapped[str | None] = mapped_column(String(25))
    income_pattern: Mapped[str | None] = mapped_column(String(15))
    declared_monthly_income_min_inr: Mapped[int | None] = mapped_column(Integer)
    declared_monthly_income_max_inr: Mapped[int | None] = mapped_column(Integer)
    household_size: Mapped[int | None] = mapped_column(SmallInteger)
    dependents_count: Mapped[int | None] = mapped_column(SmallInteger)
    annual_household_income_inr: Mapped[int | None] = mapped_column(Integer)
    land_holding_hectares: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    social_category: Mapped[str | None] = mapped_column(String(20))
    has_bank_account: Mapped[bool | None] = mapped_column(Boolean)
    is_land_owner: Mapped[bool | None] = mapped_column(Boolean)
    is_bpl_household: Mapped[bool | None] = mapped_column(Boolean)
    is_income_tax_payer: Mapped[bool | None] = mapped_column(Boolean)
    is_student: Mapped[bool | None] = mapped_column(Boolean)
    is_street_vendor: Mapped[bool | None] = mapped_column(Boolean)
    is_unorganised_worker: Mapped[bool | None] = mapped_column(Boolean)
    is_traditional_artisan: Mapped[bool | None] = mapped_column(Boolean)
    has_pucca_house: Mapped[bool | None] = mapped_column(Boolean)
    has_girl_child_below_10: Mapped[bool | None] = mapped_column(Boolean)
    is_head_of_household: Mapped[bool | None] = mapped_column(Boolean)
    is_govt_employee: Mapped[bool | None] = mapped_column(Boolean)
    confidence_answers: Mapped[list | None] = mapped_column(JSONB)
    confidence_score_pct: Mapped[int | None] = mapped_column(SmallInteger)
    confidence_level: Mapped[str | None] = mapped_column(String(10))
    voice_reply_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="profile", lazy="raise")


class Consent(UUIDPk, CreatedAt, Base):
    __tablename__ = "consents"
    __table_args__ = (check_in("consent_type", enums.CONSENT_TYPES),)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    consent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[str] = mapped_column(String(10), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)


Index("ix_consents_user_type_created", Consent.user_id, Consent.consent_type, Consent.created_at.desc())


class DeviceToken(UUIDPk, CreatedAt, Base):
    __tablename__ = "device_tokens"
    __table_args__ = (check_in("platform", enums.PLATFORMS),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expo_push_token: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    platform: Mapped[str] = mapped_column(String(10), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class NotificationSettings(UpdatedAt, Base):
    __tablename__ = "notification_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    daily_insight_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    daily_insight_time: Mapped[time] = mapped_column(Time, nullable=False, server_default=text("'09:00'"), default=time(9, 0))
    income_reminder_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    goal_reminder_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    scheme_deadline_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    lean_month_alert_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    streak_reminder_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    streak_reminder_time: Mapped[time] = mapped_column(Time, nullable=False, server_default=text("'20:00'"), default=time(20, 0))
