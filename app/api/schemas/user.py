from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

EmailString = Annotated[
    str,
    Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailString


class UserPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailString | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailString
    created_at: datetime | None = None
    is_active: bool
