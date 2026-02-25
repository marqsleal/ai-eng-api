from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.settings import settings

db_engine = create_async_engine(settings.async_connection_string, pool_pre_ping=True)


SessionLocal = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)


Base = declarative_base()
