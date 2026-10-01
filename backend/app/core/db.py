"""Async SQLAlchemy engine, declarative Base and session dependency."""

import uuid
from collections.abc import AsyncIterator, Iterable
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, MetaData, Uuid, func, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings

# Deterministic constraint names so Alembic autogenerate produces stable migrations.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# --- Column conventions (spec §6) -------------------------------------------------

class UUIDPk:
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )


class CreatedAt:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UpdatedAt:
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Timestamps(CreatedAt, UpdatedAt):
    pass


def sql_list(values: Iterable[str]) -> str:
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def check_in(column: str, values: Iterable[str], name: str | None = None) -> CheckConstraint:
    """CHECK (column IN (...)) — text enums per spec §6 conventions. NULL passes (SQL semantics)."""
    expr = f"{column} IN ({sql_list(values)})"
    return CheckConstraint(expr, name=name or f"{column}_valid")


def check_range(column: str, lo: float | None = None, hi: float | None = None, name: str | None = None) -> CheckConstraint:
    parts = []
    if lo is not None:
        parts.append(f"{column} >= {lo}")
    if hi is not None:
        parts.append(f"{column} <= {hi}")
    return CheckConstraint(" AND ".join(parts), name=name or f"{column}_range")


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args={"server_settings": {"timezone": "UTC"}},
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request, rolled back on error."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
