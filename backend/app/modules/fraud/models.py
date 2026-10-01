"""fraud_patterns, fraud_checks, fraud_reports (spec §5.7, §6.1)."""

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, SmallInteger, String, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core import enums
from app.core.crypto import EncryptedText
from app.core.db import Base, CreatedAt, UpdatedAt, UUIDPk, check_in, check_range


class FraudPattern(UUIDPk, UpdatedAt, Base):
    __tablename__ = "fraud_patterns"
    __table_args__ = (
        check_in("pattern_type", enums.FRAUD_PATTERN_TYPES),
        check_range("weight", -100, 100),
    )

    code: Mapped[str] = mapped_column(String(8), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    pattern_type: Mapped[str] = mapped_column(String(10), nullable=False)
    patterns: Mapped[list] = mapped_column(JSONB, nullable=False)
    weight: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    requires_codes: Mapped[list | None] = mapped_column(JSONB)  # any-of, e.g. R09 -> ["R02","R03"]
    reason_key: Mapped[str | None] = mapped_column(String(40))
    reason_title_en: Mapped[str | None] = mapped_column(String(80))
    reason_text_en: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)


class FraudCheck(UUIDPk, CreatedAt, Base):
    __tablename__ = "fraud_checks"
    __table_args__ = (
        check_in("input_type", enums.FRAUD_INPUT_TYPES),
        check_in("source_app", enums.SOURCE_APPS),
        check_range("risk_score", 0, 100),
        check_in("verdict", enums.VERDICTS),
        check_range("classifier_score", 0, 1),
        check_in("language", enums.LANGUAGES),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    input_type: Mapped[str] = mapped_column(String(12), nullable=False)
    source_app: Mapped[str] = mapped_column(String(10), nullable=False, server_default="other", default="other")
    extracted_text: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    snippet: Mapped[str] = mapped_column(String(60), nullable=False)
    risk_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    verdict: Mapped[str] = mapped_column(String(10), nullable=False)
    matched_rules: Mapped[list] = mapped_column(JSONB, nullable=False)
    classifier_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    explanation: Mapped[dict] = mapped_column(JSONB, nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    extracted_domains: Mapped[list | None] = mapped_column(JSONB)


Index("ix_fraud_checks_user_created", FraudCheck.user_id, FraudCheck.created_at.desc())


class FraudReport(UUIDPk, CreatedAt, Base):
    __tablename__ = "fraud_reports"
    __table_args__ = (UniqueConstraint("user_id", "text_hash"),)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fraud_check_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("fraud_checks.id", ondelete="SET NULL")
    )
    # (Suggested) index: similar_reports_count looks reports up by hash across all users.
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    matched_codes: Mapped[list] = mapped_column(JSONB, nullable=False)
    extracted_domains: Mapped[list | None] = mapped_column(JSONB)
