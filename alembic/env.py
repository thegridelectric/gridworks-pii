"""Alembic environment for the `pii` schema.

The database URL comes from `sqlalchemy.url` when a caller sets it on the
Config (the test suite does), else from `gwpii.settings.Settings`
(`GWPII_DB_URL`).
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from gwpii.db.models import Base
from gwpii.settings import Settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

db_url = (
    config.get_main_option("sqlalchemy.url") or Settings().db_url.get_secret_value()
)
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
