from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.conversation import ConversationCreate, ConversationRead
from app.database.dependencies import get_db
from app.models.conversation import Conversation
from app.models.model_version import ModelVersion
from app.models.user import User

conversations_router = APIRouter(prefix="/conversations", tags=["conversations"])
DBSession = Annotated[AsyncSession, Depends(get_db)]


@conversations_router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(payload: ConversationCreate, db: DBSession):
    """Create a conversation linked to an existing user and model version.

    Expected request:
    {
      "user_id": "<uuid>",
      "model_version_id": "<uuid>",
      "prompt": "hello",
      "response": "world",
      "temperature": 0.2
    }

    Expected output (201):
    {"id": "<uuid>", "user_id": "<uuid>", "model_version_id": "<uuid>", "prompt": "hello"}
    """
    user_result = await db.execute(
        select(User).where(User.id == payload.user_id, User.is_active.is_(True))
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    model_version_result = await db.execute(
        select(ModelVersion).where(
            ModelVersion.id == payload.model_version_id,
            ModelVersion.is_active.is_(True),
        )
    )
    model_version = model_version_result.scalar_one_or_none()
    if model_version is None:
        raise HTTPException(status_code=404, detail="Model version not found")

    conversation = Conversation(**payload.model_dump())
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@conversations_router.get("", response_model=list[ConversationRead])
async def list_conversations(db: DBSession, user_id: UUID | None = None):
    """List conversations, optionally filtered by `user_id`.

    Expected request:
    GET /conversations
    GET /conversations?user_id=<uuid>

    Expected output (200):
    [{"id": "<uuid>", "user_id": "<uuid>", "model_version_id": "<uuid>", "prompt": "hello"}]
    """
    query = select(Conversation).where(Conversation.is_active.is_(True))
    if user_id is not None:
        query = query.where(Conversation.user_id == user_id)
    query = query.order_by(Conversation.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@conversations_router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(conversation_id: UUID, db: DBSession):
    """Fetch a single conversation by its UUID.

    Expected request:
    GET /conversations/{conversation_id}

    Expected output (200):
    {"id": "<uuid>", "user_id": "<uuid>", "model_version_id": "<uuid>", "prompt": "hello"}
    """
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.is_active.is_(True),
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
