import logging
import logging.config
import sys
from datetime import UTC, datetime

from pydantic import BaseModel

from app.core.settings import LogFormat, settings


class LogRecordJsonFormatter(BaseModel):
    timestamp: str
    level: str
    logger: str
    message: str
    service: str
    environment: str


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = LogRecordJsonFormatter(
            timestamp=datetime.now(UTC).isoformat(),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            service=settings.SERVICE_NAME,
            environment=settings.ENVIRONMENT.name,
        )

        return log_record.model_dump_json()


class HumanFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().isoformat()
        logger = record.name
        level = record.levelname
        message = record.getMessage()

        return f"{timestamp} | {logger:<50} | {level:<10} | {message}"


def setup_logging() -> None:
    """
    Configure global structured logging for the application.

    This function initializes the root logging configuration using
    Python's dictConfig system and applies a JSON formatter for all
    log output.

    Design Characteristics:
        - Outputs logs to stdout (container-compatible).
        - Applies structured JSON formatting.
        - Configures root logger level.
        - Preserves existing third-party loggers.

    Intended Usage:
        - Must be called once during application startup.
        - Typically invoked in the application entrypoint (main.py).

    Environment Strategy:
        - Log level should be externally configurable in production.
        - Default level is INFO for balanced verbosity and performance.

    Raises:
        ValueError:
            If the logging configuration dictionary is invalid.
    """
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "JSON": {
                "()": JsonFormatter,
            },
            "HUMAN": {"()": HumanFormatter},
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "JSON" if settings.LOG_FORMAT == LogFormat.JSON else "HUMAN",
                "stream": sys.stdout,
            }
        },
        "root": {
            "handlers": ["default"],
            "level": settings.LOG_LEVEL.name,
        },
    }

    logging.config.dictConfig(logging_config)
