"""An ephemeral Postgres (testcontainers) migrated to head by alembic, so the
suite exercises the migration the box will run, not `create_all`. Set
`GWPII_TEST_PG_URL` to use an already-running Postgres instead. Without
either, the database tests self-skip."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from alembic import command

ROOT = Path(__file__).resolve().parents[1]

# The testcontainers reaper ("ryuk") bind-mounts the Docker socket, which
# Docker Desktop on macOS refuses. The fixture stops its own container.
os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")


@pytest.fixture(scope="session")
def pg_url():
    override = os.environ.get("GWPII_TEST_PG_URL")
    if override:
        yield override
        return
    try:
        from testcontainers.community.postgres import PostgresContainer
    except ImportError:
        pytest.skip("testcontainers not installed")
    try:
        pg = PostgresContainer("postgres:16", driver="psycopg")
        pg.start()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"could not start a testcontainers Postgres: {e}")
    try:
        yield pg.get_connection_url()
    finally:
        pg.stop()


@pytest.fixture(scope="session")
def alembic_config(pg_url) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", pg_url)
    return cfg


@pytest.fixture(scope="session")
def engine(pg_url, alembic_config):
    command.upgrade(alembic_config, "head")
    eng = create_engine(pg_url, future=True)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    """A fresh session on an emptied store."""
    with engine.begin() as conn:
        for table in (
            "changes",
            "partner_labels",
            "partner_label_schemes",
            "customers",
            "installers",
        ):
            conn.execute(text(f"DELETE FROM pii.{table}"))
    factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    with factory() as s:
        yield s
