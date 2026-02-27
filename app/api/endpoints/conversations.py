from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.conversation import ConversationCreate, ConversationPatch, ConversationRead
from app.api.schemas.query import ConversationsListQuery, ConversationsOrderBy
from app.core.errors import error_responses
from app.database.dependencies import get_db
from app.services.conversation import (
    ConversationModelVersionNotFoundError,
    ConversationNotFoundError,
    ConversationProviderNotSupportedError,
    ConversationProviderUnavailableError,
    ConversationService,
    ConversationUserNotFoundError,
)

conversations_router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
    responses=error_responses(400, 404, 422, 500, 503),
)
DBSession = Annotated[AsyncSession, Depends(get_db)]


@conversations_router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(payload: ConversationCreate, db: DBSession):
    """Create a conversation linked to an existing user and model version.

    Expected request:
    {
      "user_id": "<uuid>",
      "model_version_id": "<uuid>",
      "prompt": "hello",
      "temperature": 0.2
    }

    Expected output (201):
    {"id": "<uuid>", "user_id": "<uuid>", "model_version_id": "<uuid>", "prompt": "hello"}
    """
    service = ConversationService(db)
    try:
        return await service.create(payload)
    except (ConversationUserNotFoundError, ConversationModelVersionNotFoundError) as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except ConversationProviderNotSupportedError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    except ConversationProviderUnavailableError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err


@conversations_router.get("", response_model=list[ConversationRead])
async def list_conversations(
    db: DBSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    order_by: Annotated[ConversationsOrderBy, Query()] = ConversationsOrderBy.CREATED_AT_DESC,
    user_id: UUID | None = None,
):
    """List active conversations with optional user filter, pagination, and sorting.

    Expected request:
    GET /conversations
    GET /conversations?user_id=<uuid>
    GET /conversations?limit=20&offset=0&order_by=created_at_desc

    Expected output (200):
    [{"id": "<uuid>", "user_id": "<uuid>", "model_version_id": "<uuid>", "prompt": "hello"}]
    """
    query = ConversationsListQuery(limit=limit, offset=offset, order_by=order_by)
    service = ConversationService(db)
    return await service.list(
        user_id=user_id,
        limit=query.limit,
        offset=query.offset,
        order_by=query.order_by.value,
    )


@conversations_router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(conversation_id: UUID, db: DBSession):
    """Fetch a single conversation by its UUID.

    Expected request:
    GET /conversations/{conversation_id}

    Expected output (200):
    {"id": "<uuid>", "user_id": "<uuid>", "model_version_id": "<uuid>", "prompt": "hello"}
    """
    service = ConversationService(db)
    try:
        return await service.get(conversation_id)
    except ConversationNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


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
    service = ConversationService(db)
    try:
        return await service.patch(conversation_id, payload)
    except (
        ConversationNotFoundError,
        ConversationUserNotFoundError,
        ConversationModelVersionNotFoundError,
    ) as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@conversations_router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: UUID, db: DBSession):
    """Soft delete a conversation by UUID.

    Expected request:
    DELETE /conversations/{conversation_id}

    Expected output (204):
    No Content
    """
    service = ConversationService(db)
    try:
        await service.delete(conversation_id)
    except ConversationNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
