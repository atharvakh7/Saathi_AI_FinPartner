"""insights (spec §5.9, §6.1)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core import enums
from app.core.db import Base, CreatedAt, UUIDPk, check_in


class Insight(UUIDPk, CreatedAt, Base):
    __tablename__ = "insights"
    __table_args__ = (
        check_in("type", enums.INSIGHT_TYPES),
        check_in("tone", enums.INSIGHT_TONES),
        check_in("filter_group", enums.INSIGHT_FILTER_GROUPS),
        check_in("language", enums.LANGUAGES),
        UniqueConstraint("user_id", "dedupe_key"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(4), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    tone: Mapped[str] = mapped_column(String(10), nullable=False)
    filter_group: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(String(400), nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    cta_route: Mapped[str | None] = mapped_column(String(100))
    payload: Mapped[dict | None] = mapped_column(JSONB)
    dedupe_key: Mapped[str] = mapped_column(String(80), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


Index("ix_insights_user_read_created", Insight.user_id, Insight.is_read, Insight.created_at.desc())
