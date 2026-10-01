"""notifications (spec §5.10, §6.1)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core import enums
from app.core.db import Base, CreatedAt, UUIDPk, check_in


class Notification(UUIDPk, CreatedAt, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        check_in("status", enums.NOTIFICATION_STATUSES),
        Index("ix_notifications_status_scheduled", "status", "scheduled_for"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(String(300), nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB)  # {"route": "..."}
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default="queued", default="queued")
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


Index("ix_notifications_user_created", Notification.user_id, Notification.created_at.desc())
