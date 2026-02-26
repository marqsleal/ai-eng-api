from uuid import UUID

from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at_desc",
    ) -> list[User]:
        if order_by == "created_at_asc":
            order_clause = asc(User.created_at)
        elif order_by == "email_asc":
            order_clause = asc(User.email)
        elif order_by == "email_desc":
            order_clause = desc(User.email)
        else:
            order_clause = desc(User.created_at)

        result = await self.session.execute(
            select(User)
            .where(User.is_active.is_(True))
            .order_by(order_clause)
            .offset(offset)
            .limit(limit)
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
