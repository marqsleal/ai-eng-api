from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

NonEmptyString = Annotated[str, Field(min_length=1, max_length=128)]


class ModelVersionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: NonEmptyString
    model_name: NonEmptyString
    version_tag: NonEmptyString


class ModelVersionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: NonEmptyString | None = None
    model_name: NonEmptyString | None = None
    version_tag: NonEmptyString | None = None


class ModelVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: NonEmptyString
    model_name: NonEmptyString
    version_tag: NonEmptyString
    created_at: datetime | None = None
    is_active: bool
