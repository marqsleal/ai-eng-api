from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.conversation import ConversationCreate, ConversationPatch
from app.models.conversation import Conversation
from app.repositories.conversation import ConversationRepository
from app.repositories.model_version import ModelVersionRepository
from app.repositories.user import UserRepository
from app.services.llm.base import (
    LLMError,
    LLMProviderNotSupportedError,
    LLMResponseValidationError,
    LLMTransportError,
)
from app.services.llm.service import generate_conversation_response


class ConversationServiceError(Exception):
    pass


class ConversationNotFoundError(ConversationServiceError):
    pass


class ConversationUserNotFoundError(ConversationServiceError):
    pass


class ConversationModelVersionNotFoundError(ConversationServiceError):
    pass


class ConversationProviderNotSupportedError(ConversationServiceError):
    pass


class ConversationProviderUnavailableError(ConversationServiceError):
    pass


class ConversationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repository = UserRepository(session)
        self.model_version_repository = ModelVersionRepository(session)
        self.conversation_repository = ConversationRepository(session)

    async def create(self, payload: ConversationCreate) -> Conversation:
        user = await self.user_repository.get_active_by_id(payload.user_id)
        if user is None:
            raise ConversationUserNotFoundError("User not found")

        model_version = await self.model_version_repository.get_active_by_id(
            payload.model_version_id
        )
        if model_version is None:
            raise ConversationModelVersionNotFoundError("Model version not found")

        conversation_data = payload.model_dump()
        should_generate_response = payload.response is None or payload.response.strip() == ""
        if should_generate_response:
            try:
                llm_response = await generate_conversation_response(
                    model_version=model_version,
                    prompt=payload.prompt,
                    temperature=payload.temperature,
                    top_p=payload.top_p,
                    max_tokens=payload.max_tokens,
                )
            except LLMProviderNotSupportedError as err:
                raise ConversationProviderNotSupportedError(str(err)) from err
            except (LLMTransportError, LLMResponseValidationError) as err:
                raise ConversationProviderUnavailableError("LLM provider unavailable") from err
            except LLMError as err:
                raise ConversationProviderUnavailableError(str(err)) from err

            conversation_data["response"] = llm_response.response
            conversation_data["input_tokens"] = llm_response.input_tokens
            conversation_data["output_tokens"] = llm_response.output_tokens
            conversation_data["total_tokens"] = llm_response.total_tokens
            conversation_data["latency_ms"] = llm_response.latency_ms

        conversation = await self.conversation_repository.create(conversation_data)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def list(
        self,
        *,
        user_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at_desc",
    ) -> list[Conversation]:
        return await self.conversation_repository.list_active(
            user_id=user_id,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )

    async def get(self, conversation_id: UUID) -> Conversation:
        conversation = await self.conversation_repository.get_active_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError("Conversation not found")
        return conversation

    async def patch(self, conversation_id: UUID, payload: ConversationPatch) -> Conversation:
        conversation = await self.get(conversation_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return conversation

        if "user_id" in updates:
            user = await self.user_repository.get_active_by_id(updates["user_id"])
            if user is None:
                raise ConversationUserNotFoundError("User not found")

        if "model_version_id" in updates:
            model_version = await self.model_version_repository.get_active_by_id(
                updates["model_version_id"]
            )
            if model_version is None:
                raise ConversationModelVersionNotFoundError("Model version not found")

        for field, value in updates.items():
            setattr(conversation, field, value)

        await self.conversation_repository.persist(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def delete(self, conversation_id: UUID) -> None:
        conversation = await self.get(conversation_id)
        conversation.is_active = False
        await self.session.commit()
