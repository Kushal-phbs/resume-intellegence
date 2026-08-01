from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies.auth import get_current_user
from app.dependencies.chat import get_chat_service
from app.llm.models import LLMRequest, LLMResponse
from app.models.user import User
from app.schemas.chat import (
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=LLMResponse)
async def chat_endpoint(
    request: LLMRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> LLMResponse:
    """Receive an LLM request and return the generated response."""
    return await chat_service.chat(request)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations_endpoint(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> list[ConversationResponse]:
    """List conversations for the authenticated user."""
    return await chat_service.list_conversations(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation_endpoint(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationResponse:
    """Create a conversation for the authenticated user."""
    return await chat_service.create_conversation(
        user_id=current_user.id,
        title=payload.title,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_endpoint(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationResponse:
    """Return one conversation owned by the authenticated user."""
    return await chat_service.get_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def rename_conversation_endpoint(
    conversation_id: UUID,
    payload: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationResponse:
    """Rename one conversation owned by the authenticated user."""
    return await chat_service.rename_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
        title=payload.title,
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation_endpoint(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> Response:
    """Delete one conversation owned by the authenticated user."""
    await chat_service.delete_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
async def list_messages_endpoint(
    conversation_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> list[MessageResponse]:
    """List messages for a conversation owned by the authenticated user."""
    return await chat_service.list_messages(
        user_id=current_user.id,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message_endpoint(
    conversation_id: UUID,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Persist one user message and generated assistant response."""
    (
        conversation,
        user_message,
        assistant_message,
        token_usage,
        processing_time,
    ) = await chat_service.send_message(
        user_id=current_user.id,
        conversation_id=conversation_id,
        content=payload.content,
    )
    return ChatResponse(
        conversation=conversation,
        user_message=user_message,
        assistant_message=assistant_message,
        token_usage=token_usage,
        processing_time=processing_time,
    )
