from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.is_active.is_(True)).order_by(User.created_at.desc())
        )
        return result.scalars().all()

    async def get_active_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def create(self, email: str) -> User:
        user = User(email=email)
        self.session.add(user)
        await self.session.flush()
        return user

    async def persist(self, user: User) -> User:
        await self.session.flush()
        return user
