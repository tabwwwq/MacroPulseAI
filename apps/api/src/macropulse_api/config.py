"""Application settings, loaded from environment variables and the repository `.env` file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# apps/api/src/macropulse_api/config.py -> repository root is four levels up.
REPO_ROOT = Path(__file__).resolve().parents[4]


def _default_database_url() -> str:
    """SQLite file for frictionless local development. Production/compose uses PostgreSQL."""
    return f"sqlite:///{(REPO_ROOT / 'data' / 'local' / 'macropulse.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    database_url: str = Field(default_factory=_default_database_url)
    api_cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    # Server-side only. Never logged, never returned by the API (only whether it is configured).
    fred_api_key: SecretStr | None = None
    # Trained model artifacts. The API only ever loads artifacts from inside this directory.
    models_dir: Path = REPO_ROOT / "models" / "artifacts"

    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [o.strip() for o in value.split(",") if o.strip()]
        return value

    @field_validator("fred_api_key", mode="before")
    @classmethod
    def _empty_key_is_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("api_cors_origins")
    @classmethod
    def _no_wildcard_origins(cls, value: list[str]) -> list[str]:
        if "*" in value:
            msg = "Wildcard CORS origins are not allowed; list explicit origins."
            raise ValueError(msg)
        return value

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
