"""conversations, messages (spec §6.1). messages.content is Fernet-encrypted."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core import enums
from app.core.crypto import EncryptedText
from app.core.db import Base, CreatedAt, UUIDPk, check_in


class Conversation(UUIDPk, CreatedAt, Base):
    __tablename__ = "conversations"
    __table_args__ = (check_in("channel", enums.CHANNELS),)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(String(12), nullable=False)
    title: Mapped[str | None] = mapped_column(String(80))
    summary: Mapped[str | None] = mapped_column(Text)
    summary_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)


Index("ix_conversations_user_last_message", Conversation.user_id, Conversation.last_message_at.desc())


class Message(UUIDPk, CreatedAt, Base):
    __tablename__ = "messages"
    __table_args__ = (
        check_in("role", enums.MESSAGE_ROLES),
        check_in("language", enums.LANGUAGES),
        check_in("input_mode", enums.INPUT_MODES),
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    language: Mapped[str | None] = mapped_column(String(2))
    input_mode: Mapped[str] = mapped_column(String(6), nullable=False, server_default="text", default="text")
    intent: Mapped[str | None] = mapped_column(String(20))
    tool_calls: Mapped[list | dict | None] = mapped_column(JSONB)
    cards: Mapped[list | None] = mapped_column(JSONB)
    highlighted_terms: Mapped[list | None] = mapped_column(JSONB)
    suggested_replies: Mapped[list | None] = mapped_column(JSONB)
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
