from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.model_version import ModelVersionCreate, ModelVersionRead
from app.database.dependencies import get_db
from app.models.model_version import ModelVersion

model_versions_router = APIRouter(prefix="/model-versions", tags=["model-versions"])
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
    model_version = ModelVersion(
        provider=payload.provider,
        model_name=payload.model_name,
        version_tag=payload.version_tag,
    )
    db.add(model_version)
    await db.commit()
    await db.refresh(model_version)
    return model_version


@model_versions_router.get("", response_model=list[ModelVersionRead])
async def list_model_versions(db: DBSession):
    """List all model versions ordered by newest creation time first.

    Expected request:
    GET /model-versions

    Expected output (200):
    [{"id": "<uuid>", "provider": "openai", "model_name": "gpt-4.1", "version_tag": "v1"}]
    """
    result = await db.execute(
        select(ModelVersion)
        .where(ModelVersion.is_active.is_(True))
        .order_by(ModelVersion.created_at.desc())
    )
    return result.scalars().all()


@model_versions_router.get("/{model_version_id}", response_model=ModelVersionRead)
async def get_model_version(model_version_id: UUID, db: DBSession):
    """Fetch a single model version by its UUID.

    Expected request:
    GET /model-versions/{model_version_id}

    Expected output (200):
    {"id": "<uuid>", "provider": "openai", "model_name": "gpt-4.1", "version_tag": "v1"}
    """
    result = await db.execute(
        select(ModelVersion).where(
            ModelVersion.id == model_version_id,
            ModelVersion.is_active.is_(True),
        )
    )
    model_version = result.scalar_one_or_none()
    if model_version is None:
        raise HTTPException(status_code=404, detail="Model version not found")
    return model_version
