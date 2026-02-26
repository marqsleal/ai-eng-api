from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.model_version import ModelVersionCreate, ModelVersionPatch, ModelVersionRead
from app.api.schemas.query import ModelVersionsListQuery
from app.core.errors import error_responses
from app.database.dependencies import get_db
from app.repositories.conversation import ConversationRepository
from app.repositories.model_version import ModelVersionRepository

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
    model_version_repository = ModelVersionRepository(db)
    model_version = await model_version_repository.create(
        provider=payload.provider,
        model_name=payload.model_name,
        version_tag=payload.version_tag,
    )
    await db.commit()
    await db.refresh(model_version)
    return model_version


@model_versions_router.get("", response_model=list[ModelVersionRead])
async def list_model_versions(
    db: DBSession,
    query: Annotated[ModelVersionsListQuery, Depends(ModelVersionsListQuery)],
):
    """List active model versions with typed pagination and sorting.

    Expected request:
    GET /model-versions
    GET /model-versions?limit=20&offset=0&order_by=model_name_asc

    Expected output (200):
    [{"id": "<uuid>", "provider": "openai", "model_name": "gpt-4.1", "version_tag": "v1"}]
    """
    model_version_repository = ModelVersionRepository(db)
    return await model_version_repository.list_active(
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
    model_version_repository = ModelVersionRepository(db)
    model_version = await model_version_repository.get_active_by_id(model_version_id)
    if model_version is None:
        raise HTTPException(status_code=404, detail="Model version not found")
    return model_version


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
    model_version_repository = ModelVersionRepository(db)
    model_version = await model_version_repository.get_active_by_id(model_version_id)
    if model_version is None:
        raise HTTPException(status_code=404, detail="Model version not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return model_version

    for field, value in updates.items():
        setattr(model_version, field, value)

    await model_version_repository.persist(model_version)
    await db.commit()
    await db.refresh(model_version)
    return model_version


@model_versions_router.delete("/{model_version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_version(model_version_id: UUID, db: DBSession):
    """Soft delete a model version by UUID.

    Related active conversations are also soft deleted.

    Expected request:
    DELETE /model-versions/{model_version_id}

    Expected output (204):
    No Content
    """
    model_version_repository = ModelVersionRepository(db)
    conversation_repository = ConversationRepository(db)
    model_version = await model_version_repository.get_active_by_id(model_version_id)
    if model_version is None:
        raise HTTPException(status_code=404, detail="Model version not found")

    model_version.is_active = False
    conversations = await conversation_repository.list_active_by_model_version_id(model_version_id)
    for conversation in conversations:
        conversation.is_active = False
    await db.commit()
