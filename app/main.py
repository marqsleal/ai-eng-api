from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.endpoints.health import router as health_router
from app.core.logging import get_logger, setup_logging
from app.core.observability import setup_telemetry
from app.core.settings import settings

setup_logging()
logger = get_logger(__name__)


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


def include_counters(app: FastAPI) -> FastAPI:
    # app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(health_router)
    return app


def app_factory() -> FastAPI:
    app = FastAPI(title=settings.SERVICE_NAME, debug=settings.DEBUG, lifespan=lifespan)
    include_counters(app)
    setup_telemetry(app)
    return app


app = app_factory()
