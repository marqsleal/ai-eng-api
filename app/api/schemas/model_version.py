from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ModelVersionCreate(BaseModel):
    provider: str
    model_name: str
    version_tag: str


class ModelVersionPatch(BaseModel):
    provider: str | None = None
    model_name: str | None = None
    version_tag: str | None = None


class ModelVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    model_name: str
    version_tag: str
    created_at: datetime | None = None
    is_active: bool
