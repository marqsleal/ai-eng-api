from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    user_id: UUID
    model_version_id: UUID
    prompt: str
    response: str
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: int | None = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    model_version_id: UUID
    prompt: str
    response: str
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: int | None = None
    created_at: datetime | None = None
    is_active: bool
