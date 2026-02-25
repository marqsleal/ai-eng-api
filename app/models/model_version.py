import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.session import Base


class ModelVersion(Base):
    __tablename__ = "model_version"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    provider = Column(String, nullable=False)

    model_name = Column(String, nullable=False)

    version_tag = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
