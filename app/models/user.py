import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
