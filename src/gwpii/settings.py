"""Operator environment: `GWPII_DB_URL` and `GWPII_OPERATOR`, from `.env`.

Both are required. The URL reaches the store's loopback Postgres over an
ssh tunnel; the operator is written as `who` on every change record.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: SecretStr
    operator: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="gwpii_",
        extra="ignore",
    )


def load_settings() -> Settings:
    """Read the operator environment. Pydantic-settings fills the fields from
    the environment; the call takes no arguments."""
    return Settings()  # pyright: ignore[reportCallIssue]
