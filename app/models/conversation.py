import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.session import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    model_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=False)

    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)

    temperature = Column(Float)
    top_p = Column(Float)
    max_tokens = Column(Integer)

    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)

    latency_ms = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
