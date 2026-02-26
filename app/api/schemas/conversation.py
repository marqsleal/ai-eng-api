from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PromptString = Annotated[str, Field(min_length=1)]
ResponseString = Annotated[str, Field(min_length=1)]
TemperatureFloat = Annotated[float, Field(ge=0.0, le=2.0)]
TopPFloat = Annotated[float, Field(ge=0.0, le=1.0)]
PositiveInt = Annotated[int, Field(ge=0)]
MaxTokensInt = Annotated[int, Field(ge=1)]


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    model_version_id: UUID
    prompt: PromptString
    response: ResponseString | None = None
    temperature: TemperatureFloat | None = None
    top_p: TopPFloat | None = None
    max_tokens: MaxTokensInt | None = None
    input_tokens: PositiveInt | None = None
    output_tokens: PositiveInt | None = None
    total_tokens: PositiveInt | None = None
    latency_ms: PositiveInt | None = None


class ConversationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID | None = None
    model_version_id: UUID | None = None
    prompt: PromptString | None = None
    response: ResponseString | None = None
    temperature: TemperatureFloat | None = None
    top_p: TopPFloat | None = None
    max_tokens: MaxTokensInt | None = None
    input_tokens: PositiveInt | None = None
    output_tokens: PositiveInt | None = None
    total_tokens: PositiveInt | None = None
    latency_ms: PositiveInt | None = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    model_version_id: UUID
    prompt: PromptString
    response: ResponseString
    temperature: TemperatureFloat | None = None
    top_p: TopPFloat | None = None
    max_tokens: MaxTokensInt | None = None
    input_tokens: PositiveInt | None = None
    output_tokens: PositiveInt | None = None
    total_tokens: PositiveInt | None = None
    latency_ms: PositiveInt | None = None
    created_at: datetime | None = None
    is_active: bool
