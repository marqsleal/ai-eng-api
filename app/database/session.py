from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.settings import settings

# TODO: refatorar engine para um nome menos genérico
engine = create_engine(
    settings.connection_string,
    pool_pre_ping=True,  # avoids stale connections
    pool_size=10,  # allow concurrency scalling
    max_overflow=20,
)


SessionLocal = sessionmaker(
    autocommit=False,  # ensures transaction control
    autoflush=False,
    bind=engine,
)


Base = declarative_base()
