from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.user import UserCreate, UserPatch, UserRead
from app.database.dependencies import get_db
from app.models.conversation import Conversation
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


@users_router.patch("/{user_id}", response_model=UserRead)
async def patch_user(user_id: UUID, payload: UserPatch, db: DBSession):
    """Partially update a user by UUID.

    Expected request:
    PATCH /users/{user_id}
    {"email": "bea@example.com"}

    Expected output (200):
    {"id": "<uuid>", "email": "bea@example.com", "created_at": "<iso-datetime>",
    "is_active": true}
    """
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return user

    for field, value in updates.items():
        setattr(user, field, value)

    try:
        await db.commit()
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists") from err

    await db.refresh(user)
    return user


@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, db: DBSession):
    """Soft delete a user by UUID.

    Related active conversations are also soft deleted.

    Expected request:
    DELETE /users/{user_id}

    Expected output (204):
    No Content
    """
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    conversations_result = await db.execute(
        select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.is_active.is_(True),
        )
    )
    for conversation in conversations_result.scalars().all():
        conversation.is_active = False
    await db.commit()
