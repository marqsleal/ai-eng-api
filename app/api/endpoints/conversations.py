from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.conversation import ConversationCreate, ConversationRead
from app.database.dependencies import get_db
from app.models.conversation import Conversation
from app.models.model_version import ModelVersion
from app.models.user import User

conversations_router = APIRouter(prefix="/conversations", tags=["conversations"])
DBSession = Annotated[Session, Depends(get_db)]


@conversations_router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, db: DBSession):
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
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db.get(ModelVersion, payload.model_version_id) is None:
        raise HTTPException(status_code=404, detail="Model version not found")

    conversation = Conversation(**payload.model_dump())
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@conversations_router.get("", response_model=list[ConversationRead])
def list_conversations(db: DBSession, user_id: UUID | None = None):
    """List conversations, optionally filtered by `user_id`.

    Expected request:
    GET /conversations
    GET /conversations?user_id=<uuid>

    Expected output (200):
    [{"id": "<uuid>", "user_id": "<uuid>", "model_version_id": "<uuid>", "prompt": "hello"}]
    """
    query = db.query(Conversation).order_by(Conversation.created_at.desc())
    if user_id is not None:
        query = query.filter(Conversation.user_id == user_id)
    return query.all()


@conversations_router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation(conversation_id: UUID, db: DBSession):
    """Fetch a single conversation by its UUID.

    Expected request:
    GET /conversations/{conversation_id}

    Expected output (200):
    {"id": "<uuid>", "user_id": "<uuid>", "model_version_id": "<uuid>", "prompt": "hello"}
    """
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
