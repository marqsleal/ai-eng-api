from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self, user_id: UUID | None = None) -> list[Conversation]:
        query = select(Conversation).where(Conversation.is_active.is_(True))
        if user_id is not None:
            query = query.where(Conversation.user_id == user_id)
        query = query.order_by(Conversation.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_active_by_user_id(self, user_id: UUID) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.is_active.is_(True),
            )
        )
        return result.scalars().all()

    async def list_active_by_model_version_id(self, model_version_id: UUID) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation).where(
                Conversation.model_version_id == model_version_id,
                Conversation.is_active.is_(True),
            )
        )
        return result.scalars().all()

    async def get_active_by_id(self, conversation_id: UUID) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, payload: dict) -> Conversation:
        conversation = Conversation(**payload)
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def persist(self, conversation: Conversation) -> Conversation:
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def commit(self) -> None:
        await self.session.commit()
