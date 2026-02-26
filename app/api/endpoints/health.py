import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import error_responses
from app.core.settings import Environment, settings
from app.database.dependencies import get_db

logger = logging.getLogger(__name__)
health_router = APIRouter(responses=error_responses(503, 500))

DBSession = Annotated[AsyncSession, Depends(get_db)]


@health_router.get("/health/db")
async def db_health_deck(db: DBSession):
    """Run a lightweight DB query to verify database connectivity.

    Expected request:
    GET /health/db

    Expected output (200):
    {"status": "ok"}
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as err:
        logger.error("DB health check failed")
        if settings.ENVIRONMENT == Environment.DEV:
            raise HTTPException(status_code=503, detail=f"Database Unavailable: {err}") from err
        raise HTTPException(status_code=503, detail="Database Unavailable") from err
