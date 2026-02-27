from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.user import UserPatch
from app.models.user import User
from app.repositories.conversation import ConversationRepository
from app.repositories.user import UserRepository


class UserServiceError(Exception):
    pass


class UserNotFoundError(UserServiceError):
    pass


class UserConflictError(UserServiceError):
    pass


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repository = UserRepository(session)
        self.conversation_repository = ConversationRepository(session)

    async def create(self, email: str) -> User:
        try:
            user = await self.user_repository.create(email)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except IntegrityError as err:
            await self.session.rollback()
            raise UserConflictError("Email already exists") from err

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at_desc",
    ) -> list[User]:
        return await self.user_repository.list_active(
            limit=limit,
            offset=offset,
            order_by=order_by,
        )

    async def get(self, user_id: UUID) -> User:
        user = await self.user_repository.get_active_by_id(user_id)
        if user is None:
            raise UserNotFoundError("User not found")
        return user

    async def patch(self, user_id: UUID, payload: UserPatch) -> User:
        user = await self.get(user_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return user

        for field, value in updates.items():
            setattr(user, field, value)

        try:
            await self.user_repository.persist(user)
            await self.session.commit()
            await self.session.refresh(user)
        except IntegrityError as err:
            await self.session.rollback()
            raise UserConflictError("Email already exists") from err
        return user

    async def delete(self, user_id: UUID) -> None:
        user = await self.get(user_id)
        user.is_active = False
        for conversation in await self.conversation_repository.list_active_by_user_id(user_id):
            conversation.is_active = False
        await self.session.commit()
