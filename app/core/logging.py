import json
import logging
import logging.config
import sys
from datetime import datetime
from typing import Any

from app.core.settings import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.SERVICE_NAME,
            "environment": settings.ENVIRONMENT,
        }

        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


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
    log_level = settings.LOG_LEVEL

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JsonFormatter,
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": sys.stdout,
            }
        },
        "root": {
            "handlers": ["default"],
            "level": log_level,
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a module-scoped logger instance.

    This function provides a consistent mechanism for obtaining
    logger instances across the application while maintaining
    centralized configuration control.

    Args:
        name (str):
            The logger name. Typically use `__name__` for
            module-level traceability.

    Returns:
        logging.Logger:
            Configured logger instance inheriting global settings.

    Example:
        `logger = get_logger(__name__)`
    """
    return logging.getLogger(name)
