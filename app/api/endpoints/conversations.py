from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.conversation import ConversationCreate, ConversationPatch, ConversationRead
from app.database.dependencies import get_db
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
      "response": "world (optional, generated when omitted)",
      "temperature": 0.2
    }

    Expected output (201):
    {"id": "<uuid>", "user_id": "<uuid>", "model_version_id": "<uuid>", "prompt": "hello"}
    """
    user_repository = UserRepository(db)
    model_version_repository = ModelVersionRepository(db)
    conversation_repository = ConversationRepository(db)

    user = await user_repository.get_active_by_id(payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    model_version = await model_version_repository.get_active_by_id(payload.model_version_id)
    if model_version is None:
        raise HTTPException(status_code=404, detail="Model version not found")

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
            raise HTTPException(status_code=400, detail=str(err)) from err
        except (LLMTransportError, LLMResponseValidationError) as err:
            raise HTTPException(status_code=503, detail="LLM provider unavailable") from err
        except LLMError as err:
            raise HTTPException(status_code=503, detail=str(err)) from err

        conversation_data["response"] = llm_response.response
        conversation_data["input_tokens"] = llm_response.input_tokens
        conversation_data["output_tokens"] = llm_response.output_tokens
        conversation_data["total_tokens"] = llm_response.total_tokens
        conversation_data["latency_ms"] = llm_response.latency_ms

    conversation = await conversation_repository.create(conversation_data)
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
    conversation_repository = ConversationRepository(db)
    return await conversation_repository.list_active(user_id=user_id)


@conversations_router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(conversation_id: UUID, db: DBSession):
    """Fetch a single conversation by its UUID.

    Expected request:
    GET /conversations/{conversation_id}

    Expected output (200):
    {"id": "<uuid>", "user_id": "<uuid>", "model_version_id": "<uuid>", "prompt": "hello"}
    """
    conversation_repository = ConversationRepository(db)
    conversation = await conversation_repository.get_active_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@conversations_router.patch("/{conversation_id}", response_model=ConversationRead)
async def patch_conversation(conversation_id: UUID, payload: ConversationPatch, db: DBSession):
    """Partially update a conversation by UUID.

    Expected request:
    PATCH /conversations/{conversation_id}
    {"prompt": "new prompt", "temperature": 0.3}

    Expected output (200):
    {"id": "<uuid>", "user_id": "<uuid>", "model_version_id": "<uuid>", "prompt": "new prompt",
    "response": "world", "temperature": 0.3, "created_at": "<iso-datetime>", "is_active": true}
    """
    conversation_repository = ConversationRepository(db)
    user_repository = UserRepository(db)
    model_version_repository = ModelVersionRepository(db)
    conversation = await conversation_repository.get_active_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return conversation

    if "user_id" in updates:
        user = await user_repository.get_active_by_id(updates["user_id"])
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

    if "model_version_id" in updates:
        model_version = await model_version_repository.get_active_by_id(updates["model_version_id"])
        if model_version is None:
            raise HTTPException(status_code=404, detail="Model version not found")

    for field, value in updates.items():
        setattr(conversation, field, value)

    await conversation_repository.persist(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@conversations_router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: UUID, db: DBSession):
    """Soft delete a conversation by UUID.

    Expected request:
    DELETE /conversations/{conversation_id}

    Expected output (204):
    No Content
    """
    conversation_repository = ConversationRepository(db)
    conversation = await conversation_repository.get_active_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.is_active = False
    await db.commit()
