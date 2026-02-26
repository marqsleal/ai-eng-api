from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogFormat(Enum):
    JSON = "JSON"
    HUMAN = "HUMAN"


class Environment(Enum):
    DEV = "DEV"
    HML = "HML"
    PRD = "PRD"


class LogLevel(Enum):
    INFO = "INFO"
    DEBUG = "DEBUG"


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
    )

    SERVICE_NAME: str = Field(default="ai-eng-api")
    ENVIRONMENT: Environment = Environment.DEV
    LOG_LEVEL: LogLevel = LogLevel.DEBUG
    LOG_FORMAT: LogFormat = LogFormat.HUMAN

    API_VI_PREFIX: str = Field(default="/api/v1")
    DEBUG: bool = Field(default=False)
    OPENAPI_ENABLED: bool = Field(default=True)
    OPENAPI_JSON_PATH: str = Field(default="/openapi.json")
    SWAGGER_UI_ENABLED: bool = Field(default=True)
    SWAGGER_UI_PATH: str = Field(default="/docs")
    API_DESCRIPTION: str = Field(default="FastAPI backend for AI workflows.")

    REDIS_URL: str | None = None
    VECTOR_DB_URL: str | None = None
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_DEFAULT_MODEL: str = Field(default="llama3.2:3b")
    OLLAMA_TIMEOUT_SECONDS: float = Field(default=30.0)
    OLLAMA_STARTUP_CHECK_ENABLED: bool = Field(default=True)

    VERSION: str = Field(default="1.0.0")
    OTEL_EXPORTER_OTLP_ENDPOINT: str

    POSTGRES_HOSTNAME: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = Field(5432)

    @property
    def connection_string(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOSTNAME}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def async_connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOSTNAME}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    """
    return Settings()


settings = get_settings()
