from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints.health import health_router
from app.core.logging import get_logger, setup_logging
from app.core.observability import setup_telemetry
from app.core.settings import settings

setup_logging()
logger = get_logger(__name__)

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
    setup_telemetry(app)
    return app


app = app_factory()
