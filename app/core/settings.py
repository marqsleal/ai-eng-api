from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application configuration.

    This class loads environment variables from .env or system variables

    All fields are strongly typed and validated at startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        # extra="ignore"
    )

    SERVICE_NAME: str = Field(default="ai-eng-api")
    ENVIRONMENT: str = Field(default="dev")
    LOG_LEVEL: str = Field(default="INFO")

    API_VI_PREFIX: str = Field(default="/api/v1")
    DEBUG: bool = Field(default=False)

    DATABASE_URL: str
    REDIS_URL: str | None = None
    VECTOR_DB_URL: str | None = None

    VERSION: str = Field(default="1.0.0")
    OTEL_EXPORTER_OTLP_ENDPOINT: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = Field(5432)


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    """
    return Settings()


settings = get_settings()
