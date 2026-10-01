"""otp_requests, refresh_tokens (spec §6.1)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, SmallInteger, String, Uuid, text
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, CreatedAt, UUIDPk


class OtpRequest(UUIDPk, CreatedAt, Base):
    __tablename__ = "otp_requests"

    phone_e164: Mapped[str] = mapped_column(String(16), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # HMAC-SHA256 hex
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"), default=0)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    request_ip: Mapped[str | None] = mapped_column(INET)


Index("ix_otp_requests_phone_created", OtpRequest.phone_e164, OtpRequest.created_at.desc())


class RefreshToken(UUIDPk, CreatedAt, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)  # SHA-256 hex
    device_id: Mapped[str | None] = mapped_column(String(100))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
