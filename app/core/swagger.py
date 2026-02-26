import logging

from pydantic import BaseModel, ConfigDict

from app.core.settings import Settings

logger = logging.getLogger(__name__)


class DocsConfig(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)

    docs_url: str | None
    openapi_url: str | None


def resolve_docs_config(config: Settings) -> DocsConfig:
    """Resolve docs URLs and gracefully handle incompatible flags."""
    openapi_url = config.OPENAPI_JSON_PATH if config.OPENAPI_ENABLED else None
    docs_url = config.SWAGGER_UI_PATH if config.SWAGGER_UI_ENABLED else None

    if docs_url is not None and openapi_url is None:
        logger.warning(
            "SWAGGER_UI_ENABLED is true, but OPENAPI_ENABLED is false. Swagger UI will be disabled."
        )
        docs_url = None

    return DocsConfig(docs_url=docs_url, openapi_url=openapi_url)
