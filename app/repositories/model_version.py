from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_version import ModelVersion


class ModelVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[ModelVersion]:
        result = await self.session.execute(
            select(ModelVersion)
            .where(ModelVersion.is_active.is_(True))
            .order_by(ModelVersion.created_at.desc())
        )
        return result.scalars().all()

    async def get_active_by_id(self, model_version_id: UUID) -> ModelVersion | None:
        result = await self.session.execute(
            select(ModelVersion).where(
                ModelVersion.id == model_version_id,
                ModelVersion.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, provider: str, model_name: str, version_tag: str) -> ModelVersion:
        model_version = ModelVersion(
            provider=provider,
            model_name=model_name,
            version_tag=version_tag,
        )
        self.session.add(model_version)
        await self.session.flush()
        return model_version

    async def persist(self, model_version: ModelVersion) -> ModelVersion:
        await self.session.flush()
        return model_version
