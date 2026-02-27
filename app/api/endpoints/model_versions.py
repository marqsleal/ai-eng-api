from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.model_version import ModelVersionCreate, ModelVersionPatch, ModelVersionRead
from app.api.schemas.query import ModelVersionsListQuery, ModelVersionsOrderBy
from app.core.errors import error_responses
from app.database.dependencies import get_db
from app.services.model_version import (
    ModelVersionNotFoundError,
    ModelVersionService,
)

model_versions_router = APIRouter(
    prefix="/model-versions",
    tags=["model-versions"],
    responses=error_responses(404, 422, 500),
)
DBSession = Annotated[AsyncSession, Depends(get_db)]


@model_versions_router.post(
    "",
    response_model=ModelVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_model_version(payload: ModelVersionCreate, db: DBSession):
    """Create a model version record for a provider/model pair.

    Expected request:
    {"provider": "openai", "model_name": "gpt-4.1", "version_tag": "2026-02-25"}

    Expected output (201):
    {
      "id": "<uuid>",
      "provider": "openai",
      "model_name": "gpt-4.1",
      "version_tag": "2026-02-25",
      "created_at": "<iso-datetime>"
    }
    """
    service = ModelVersionService(db)
    return await service.create(
        provider=payload.provider,
        model_name=payload.model_name,
        version_tag=payload.version_tag,
    )


@model_versions_router.get("", response_model=list[ModelVersionRead])
async def list_model_versions(
    db: DBSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    order_by: Annotated[ModelVersionsOrderBy, Query()] = ModelVersionsOrderBy.CREATED_AT_DESC,
):
    """List active model versions with typed pagination and sorting.

    Expected request:
    GET /model-versions
    GET /model-versions?limit=20&offset=0&order_by=model_name_asc

    Expected output (200):
    [{"id": "<uuid>", "provider": "openai", "model_name": "gpt-4.1", "version_tag": "v1"}]
    """
    query = ModelVersionsListQuery(limit=limit, offset=offset, order_by=order_by)
    service = ModelVersionService(db)
    return await service.list(
        limit=query.limit,
        offset=query.offset,
        order_by=query.order_by.value,
    )


@model_versions_router.get("/{model_version_id}", response_model=ModelVersionRead)
async def get_model_version(model_version_id: UUID, db: DBSession):
    """Fetch a single model version by its UUID.

    Expected request:
    GET /model-versions/{model_version_id}

    Expected output (200):
    {"id": "<uuid>", "provider": "openai", "model_name": "gpt-4.1", "version_tag": "v1"}
    """
    service = ModelVersionService(db)
    try:
        return await service.get(model_version_id)
    except ModelVersionNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@model_versions_router.patch("/{model_version_id}", response_model=ModelVersionRead)
async def patch_model_version(model_version_id: UUID, payload: ModelVersionPatch, db: DBSession):
    """Partially update a model version by UUID.

    Expected request:
    PATCH /model-versions/{model_version_id}
    {"version_tag": "2026-02-26"}

    Expected output (200):
    {"id": "<uuid>", "provider": "openai", "model_name": "gpt-4.1", "version_tag": "2026-02-26",
    "created_at": "<iso-datetime>", "is_active": true}
    """
    service = ModelVersionService(db)
    try:
        return await service.patch(model_version_id, payload)
    except ModelVersionNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@model_versions_router.delete("/{model_version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_version(model_version_id: UUID, db: DBSession):
    """Soft delete a model version by UUID.

    Related active conversations are also soft deleted.

    Expected request:
    DELETE /model-versions/{model_version_id}

    Expected output (204):
    No Content
    """
    service = ModelVersionService(db)
    try:
        await service.delete(model_version_id)
    except ModelVersionNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
