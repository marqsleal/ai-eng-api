from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.user import UserCreate, UserPatch, UserRead
from app.core.errors import error_responses
from app.database.dependencies import get_db
from app.repositories.conversation import ConversationRepository
from app.repositories.user import UserRepository

users_router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses=error_responses(404, 409, 422, 500),
)
DBSession = Annotated[AsyncSession, Depends(get_db)]


@users_router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: DBSession):
    """Create a new user using a unique email address.

    Expected request:
    {"email": "ana@example.com"}

    Expected output (201):
    {"id": "<uuid>", "email": "ana@example.com", "created_at": "<iso-datetime>"}
    """
    user_repository = UserRepository(db)
    try:
        user = await user_repository.create(payload.email)
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists") from err


@users_router.get("", response_model=list[UserRead])
async def list_users(db: DBSession):
    """List all users ordered by newest creation time first.

    Expected request:
    GET /users

    Expected output (200):
    [{"id": "<uuid>", "email": "ana@example.com", "created_at": "<iso-datetime>"}]
    """
    user_repository = UserRepository(db)
    return await user_repository.list_active()


@users_router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: UUID, db: DBSession):
    """Fetch a single user by its UUID.

    Expected request:
    GET /users/{user_id}

    Expected output (200):
    {"id": "<uuid>", "email": "ana@example.com", "created_at": "<iso-datetime>"}
    """
    user_repository = UserRepository(db)
    user = await user_repository.get_active_by_id(user_id)
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
    user_repository = UserRepository(db)
    user = await user_repository.get_active_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return user

    for field, value in updates.items():
        setattr(user, field, value)

    try:
        await user_repository.persist(user)
        await db.commit()
        await db.refresh(user)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists") from err

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
    user_repository = UserRepository(db)
    conversation_repository = ConversationRepository(db)

    user = await user_repository.get_active_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    for conversation in await conversation_repository.list_active_by_user_id(user_id):
        conversation.is_active = False
    await db.commit()
