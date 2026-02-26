import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints.conversations import conversations_router
from app.api.endpoints.health import health_router
from app.api.endpoints.model_versions import model_versions_router
from app.api.endpoints.users import users_router
from app.core.logging import setup_logging
from app.core.settings import settings

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
    app = FastAPI(title=settings.SERVICE_NAME, debug=settings.DEBUG, lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(users_router)
    app.include_router(model_versions_router)
    app.include_router(conversations_router)
    # setup_telemetry(app)
    return app


app = app_factory()
