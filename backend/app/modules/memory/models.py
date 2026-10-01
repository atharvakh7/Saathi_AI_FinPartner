"""memory_facts with pgvector embeddings (spec §5.4, §6.1)."""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, SmallInteger, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core import enums
from app.core.db import Base, CreatedAt, UUIDPk, check_in, check_range

# Fixed by the schema; EMBED_MODEL must produce vectors of this size (bge-m3 = 1024).
EMBEDDING_DIM = 1024


class MemoryFact(UUIDPk, CreatedAt, Base):
    __tablename__ = "memory_facts"
    __table_args__ = (
        check_in("category", enums.MEMORY_CATEGORIES),
        check_range("importance", 1, 5),
        Index("ix_memory_facts_user_active", "user_id", "is_active"),
        Index(
            "ix_memory_facts_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(15), nullable=False)
    fact_text: Mapped[str] = mapped_column(String(300), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    importance: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("3"), default=3)
    source_message_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="SET NULL")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
