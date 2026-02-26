from uuid import UUID

from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_version import ModelVersion


class ModelVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at_desc",
    ) -> list[ModelVersion]:
        if order_by == "created_at_asc":
            order_clause = asc(ModelVersion.created_at)
        elif order_by == "model_name_asc":
            order_clause = asc(ModelVersion.model_name)
        elif order_by == "model_name_desc":
            order_clause = desc(ModelVersion.model_name)
        else:
            order_clause = desc(ModelVersion.created_at)

        result = await self.session.execute(
            select(ModelVersion)
            .where(ModelVersion.is_active.is_(True))
            .order_by(order_clause)
            .offset(offset)
            .limit(limit)
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
