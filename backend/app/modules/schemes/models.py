"""Scheme Scout tables (spec §5.6, §6.1)."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core import enums
from app.core.db import Base, Timestamps, UpdatedAt, UUIDPk, check_in


class SchemeCategory(Base):
    __tablename__ = "scheme_categories"

    slug: Mapped[str] = mapped_column(String(30), primary_key=True)
    name_en: Mapped[str] = mapped_column(String(60), nullable=False)
    icon: Mapped[str] = mapped_column(String(30), nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class Scheme(UUIDPk, Timestamps, Base):
    __tablename__ = "schemes"
    __table_args__ = (
        check_in("level", enums.SCHEME_LEVELS),
        check_in("state_code", enums.STATE_CODES),
        CheckConstraint("level = 'central' OR state_code IS NOT NULL", name="state_scheme_has_state"),
        check_in("benefit_type", enums.BENEFIT_TYPES),
        Index("ix_schemes_level_state", "level", "state_code"),
    )

    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    level: Mapped[str] = mapped_column(String(7), nullable=False)
    state_code: Mapped[str | None] = mapped_column(String(2))
    category_slug: Mapped[str] = mapped_column(
        String(30), ForeignKey("scheme_categories.slug"), nullable=False, index=True
    )
    ministry_or_dept: Mapped[str | None] = mapped_column(String(120))
    benefit_type: Mapped[str] = mapped_column(String(15), nullable=False)
    benefit_summary_en: Mapped[str] = mapped_column(String(300), nullable=False)
    description_en: Mapped[str] = mapped_column(Text, nullable=False)
    application_mode_en: Mapped[str | None] = mapped_column(String(200))
    official_url: Mapped[str] = mapped_column(String(300), nullable=False)
    source_url: Mapped[str] = mapped_column(String(300), nullable=False)
    last_verified_on: Mapped[date] = mapped_column(Date, nullable=False)
    deadline_on: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)


class SchemeEligibilityRule(UUIDPk, Base):
    __tablename__ = "scheme_eligibility_rules"
    __table_args__ = (
        check_in("operator", enums.RULE_OPERATORS),
        UniqueConstraint("scheme_id", "rule_key"),
    )

    scheme_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    rule_key: Mapped[str] = mapped_column(String(60), nullable=False)
    field: Mapped[str] = mapped_column(String(50), nullable=False)
    operator: Mapped[str] = mapped_column(String(10), nullable=False)
    value: Mapped[object | None] = mapped_column(JSONB(none_as_null=True))  # SQL NULL, not JSON null
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    explanation_en: Mapped[str] = mapped_column(String(200), nullable=False)


class SchemeStep(UUIDPk, Base):
    __tablename__ = "scheme_steps"
    __table_args__ = (UniqueConstraint("scheme_id", "step_no"),)

    scheme_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    step_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title_en: Mapped[str] = mapped_column(String(100), nullable=False)
    description_en: Mapped[str] = mapped_column(String(400), nullable=False)


class SchemeDocument(UUIDPk, Base):
    __tablename__ = "scheme_documents"

    scheme_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_name_en: Mapped[str] = mapped_column(String(120), nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    # (Suggested) display order; ids are random UUIDs so they can't order the checklist.
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"), default=0)


class SchemeTranslation(UUIDPk, Timestamps, Base):
    __tablename__ = "scheme_translations"
    __table_args__ = (
        check_in("language", enums.TRANSLATION_LANGUAGES),
        check_in("generated_by", enums.GENERATED_BY),
        UniqueConstraint("scheme_id", "language"),
    )

    scheme_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    generated_by: Mapped[str] = mapped_column(String(5), nullable=False)
    reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)


class UserSchemeMatch(UUIDPk, Base):
    __tablename__ = "user_scheme_matches"
    __table_args__ = (
        check_in("status", enums.MATCH_STATUSES),
        UniqueConstraint("user_id", "scheme_id"),
        Index("ix_user_scheme_matches_user_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scheme_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(17), nullable=False)
    rule_results: Mapped[list] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UserSchemeTracking(UUIDPk, UpdatedAt, Base):
    __tablename__ = "user_scheme_tracking"
    __table_args__ = (
        check_in("status", enums.TRACKING_STATUSES),
        UniqueConstraint("user_id", "scheme_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scheme_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False)
