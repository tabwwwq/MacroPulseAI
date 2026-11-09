"""Alembic environment. Uses a connection passed via `config.attributes` when available
(programmatic upgrades/tests), otherwise builds an engine from MacroPulse settings."""

from __future__ import annotations

from alembic import context
from sqlalchemy.engine import Connection

from macropulse_api import models  # noqa: F401  (register tables on Base.metadata)
from macropulse_api.config import get_settings
from macropulse_api.db import Base, build_engine

config = context.config
target_metadata = Base.metadata


def _configure_and_run(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=connection.dialect.name == "sqlite",
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        _configure_and_run(connection)
        return
    engine = build_engine(get_settings().database_url)
    try:
        with engine.begin() as conn:
            _configure_and_run(conn)
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
