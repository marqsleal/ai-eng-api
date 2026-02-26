from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class UsersOrderBy(Enum):
    CREATED_AT_DESC = "created_at_desc"
    CREATED_AT_ASC = "created_at_asc"
    EMAIL_ASC = "email_asc"
    EMAIL_DESC = "email_desc"


class ModelVersionsOrderBy(Enum):
    CREATED_AT_DESC = "created_at_desc"
    CREATED_AT_ASC = "created_at_asc"
    MODEL_NAME_ASC = "model_name_asc"
    MODEL_NAME_DESC = "model_name_desc"


class ConversationsOrderBy(Enum):
    CREATED_AT_DESC = "created_at_desc"
    CREATED_AT_ASC = "created_at_asc"
    LATENCY_MS_ASC = "latency_ms_asc"
    LATENCY_MS_DESC = "latency_ms_desc"


class ListQueryBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class UsersListQuery(ListQueryBase):
    order_by: UsersOrderBy = UsersOrderBy.CREATED_AT_DESC


class ModelVersionsListQuery(ListQueryBase):
    order_by: ModelVersionsOrderBy = ModelVersionsOrderBy.CREATED_AT_DESC


class ConversationsListQuery(ListQueryBase):
    order_by: ConversationsOrderBy = ConversationsOrderBy.CREATED_AT_DESC
