"""Alembic environment (async, asyncpg). URL and metadata come from the app."""

import asyncio
from logging.config import fileConfig

from alembic import context
from pgvector.sqlalchemy import Vector
from sqlalchemy.ext.asyncio import create_async_engine

import app.models_registry  # noqa: F401  (registers all tables on Base.metadata)
from app.core.config import settings
from app.core.crypto import EncryptedText
from app.core.db import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def render_item(type_, obj, autogen_context):
    """Render app-specific column types as plain, import-stable types in migrations."""
    if type_ == "type" and isinstance(obj, EncryptedText):
        return "sa.Text()"  # Fernet tokens are stored as TEXT
    if type_ == "type" and isinstance(obj, Vector):
        autogen_context.imports.add("from pgvector.sqlalchemy import Vector")
        return f"Vector({obj.dim})"
    return False


def _configure(**kwargs) -> None:
    context.configure(
        target_metadata=target_metadata,
        render_item=render_item,
        compare_type=True,
        compare_server_default=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    _configure(url=settings.DATABASE_URL, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def _run_sync(connection) -> None:
    _configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as connection:
        await connection.run_sync(_run_sync)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
