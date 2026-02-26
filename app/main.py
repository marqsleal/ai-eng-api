import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints.conversations import conversations_router
from app.api.endpoints.health import health_router
from app.api.endpoints.model_versions import model_versions_router
from app.api.endpoints.users import users_router
from app.core.logging import setup_logging
from app.core.settings import settings
from app.core.swagger import resolve_docs_config

setup_logging()
logger = logging.getLogger(__name__)

# TODO: integrate mypi with strict mode


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Service")

    # Initialize:
    # app.state.vector_client = ...
    # app.state.redis = ...
    # app.state.embedding_model = ...
    # app.state.llm_client = ...

    yield

    logger.info("Shutting down service")


def app_factory() -> FastAPI:
    docs_config = resolve_docs_config(settings)
    app = FastAPI(
        title=settings.SERVICE_NAME,
        version=settings.VERSION,
        description=settings.API_DESCRIPTION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url=docs_config.docs_url,
        redoc_url=None,
        openapi_url=docs_config.openapi_url,
        swagger_ui_parameters={
            "displayRequestDuration": True,
            "defaultModelsExpandDepth": 1,
        },
    )
    app.include_router(health_router)
    app.include_router(users_router)
    app.include_router(model_versions_router)
    app.include_router(conversations_router)
    # setup_telemetry(app)
    return app


app = app_factory()
