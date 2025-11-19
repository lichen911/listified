"""Application settings and configuration using Pydantic."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings.

    Configuration is loaded from environment variables.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    POSTGRES_DSN: str = "postgresql+asyncpg://postgres:postgres@localhost/postgres"
    DEBUG: bool = False


settings = Settings()
