from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.model_version import ModelVersionPatch
from app.models.model_version import ModelVersion
from app.repositories.conversation import ConversationRepository
from app.repositories.model_version import ModelVersionRepository


class ModelVersionServiceError(Exception):
    pass


class ModelVersionNotFoundError(ModelVersionServiceError):
    pass


class ModelVersionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.model_version_repository = ModelVersionRepository(session)
        self.conversation_repository = ConversationRepository(session)

    async def create(self, *, provider: str, model_name: str, version_tag: str) -> ModelVersion:
        model_version = await self.model_version_repository.create(
            provider=provider,
            model_name=model_name,
            version_tag=version_tag,
        )
        await self.session.commit()
        await self.session.refresh(model_version)
        return model_version

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at_desc",
    ) -> list[ModelVersion]:
        return await self.model_version_repository.list_active(
            limit=limit,
            offset=offset,
            order_by=order_by,
        )

    async def get(self, model_version_id: UUID) -> ModelVersion:
        model_version = await self.model_version_repository.get_active_by_id(model_version_id)
        if model_version is None:
            raise ModelVersionNotFoundError("Model version not found")
        return model_version

    async def patch(self, model_version_id: UUID, payload: ModelVersionPatch) -> ModelVersion:
        model_version = await self.get(model_version_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return model_version

        for field, value in updates.items():
            setattr(model_version, field, value)

        await self.model_version_repository.persist(model_version)
        await self.session.commit()
        await self.session.refresh(model_version)
        return model_version

    async def delete(self, model_version_id: UUID) -> None:
        model_version = await self.get(model_version_id)
        model_version.is_active = False
        conversations = await self.conversation_repository.list_active_by_model_version_id(
            model_version_id
        )
        for conversation in conversations:
            conversation.is_active = False
        await self.session.commit()
