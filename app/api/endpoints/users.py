from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.user import UserCreate, UserRead
from app.database.dependencies import get_db
from app.models.user import User

users_router = APIRouter(prefix="/users", tags=["users"])
DBSession = Annotated[AsyncSession, Depends(get_db)]


@users_router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: DBSession):
    """Create a new user using a unique email address.

    Expected request:
    {"email": "ana@example.com"}

    Expected output (201):
    {"id": "<uuid>", "email": "ana@example.com", "created_at": "<iso-datetime>"}
    """
    user = User(email=payload.email)
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists") from err
    await db.refresh(user)
    return user


@users_router.get("", response_model=list[UserRead])
async def list_users(db: DBSession):
    """List all users ordered by newest creation time first.

    Expected request:
    GET /users

    Expected output (200):
    [{"id": "<uuid>", "email": "ana@example.com", "created_at": "<iso-datetime>"}]
    """
    result = await db.execute(
        select(User).where(User.is_active.is_(True)).order_by(User.created_at.desc())
    )
    return result.scalars().all()


@users_router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: UUID, db: DBSession):
    """Fetch a single user by its UUID.

    Expected request:
    GET /users/{user_id}

    Expected output (200):
    {"id": "<uuid>", "email": "ana@example.com", "created_at": "<iso-datetime>"}
    """
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
