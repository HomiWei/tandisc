"""Process settings. Secrets stay in the environment and are never logged."""

from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_port: int = 8080
    app_env: str = "local"
    database_url: str | None = None
    github_token: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    app_timezone: str = "Asia/Shanghai"

    @field_validator("app_timezone")
    @classmethod
    def _timezone_exists(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone: {value}") from exc
        return value

    @field_validator("app_port")
    @classmethod
    def _port_range(cls, value: int) -> int:
        if value < 1 or value > 65535:
            raise ValueError("APP_PORT must be between 1 and 65535")
        return value

    @property
    def zoneinfo(self) -> ZoneInfo:
        return ZoneInfo(self.app_timezone)

    @property
    def llm_ready(self) -> bool:
        return bool(
            (self.llm_base_url or "").strip()
            and (self.llm_api_key or "").strip()
            and (self.llm_model or "").strip()
        )

    @property
    def sqlalchemy_url(self) -> str:
        raw = (self.database_url or "").strip()
        if not raw:
            data_dir = BACKEND_ROOT / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            return "sqlite:///" + (data_dir / "tandisc.db").as_posix()
        if raw.startswith("postgresql+psycopg://"):
            return raw
        if raw.startswith("postgres://"):
            return "postgresql+psycopg://" + raw[len("postgres://") :]
        if raw.startswith("postgresql://"):
            return "postgresql+psycopg://" + raw[len("postgresql://") :]
        return raw


@lru_cache
def get_settings() -> Settings:
    return Settings()
