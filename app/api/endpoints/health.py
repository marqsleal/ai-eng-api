from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.settings import settings
from app.database.dependencies import get_db

logger = get_logger(__name__)
health_router = APIRouter()

DBSession = Annotated[Session, Depends(get_db)]


@health_router.get("/health/db")
def db_health_deck(db: DBSession):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as err:
        logger.error("DB health check failed")
        if settings.ENVIRONMENT == "dev":
            raise HTTPException(status_code=503, detail=f"Database Unavailable: {err}") from err
        raise HTTPException(status_code=503, detail="Database Unavailable") from err
