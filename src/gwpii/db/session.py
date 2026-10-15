"""Engine and session factory on the env-configured store, built on first use
so importing the package (for `gwpii --help`) needs no environment."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from gwpii.settings import load_settings


@lru_cache(maxsize=1)
def session_factory() -> sessionmaker[Session]:
    settings = load_settings()
    engine = create_engine(settings.db_url.get_secret_value(), future=True)
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def open_session() -> Session:
    return session_factory()()
