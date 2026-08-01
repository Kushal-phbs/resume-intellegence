from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, Response, status

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


@router.post(
    "/",
    response_model=LLMResponse,
    summary="Generate One Chat Reply",
    description=(
        "Generate a single LLM response from the provided chat prompt payload. "
        "This endpoint is stateless and does not persist conversation history."
    ),
    responses={
        200: {"description": "LLM response generated successfully."},
        400: {"description": "Invalid chat request payload."},
    },
)
async def chat_endpoint(
    request: LLMRequest = Body(
        description="Chat request containing user message and optional context."
    ),
    chat_service: ChatService = Depends(get_chat_service),
) -> LLMResponse:
    """Receive an LLM request and return the generated response."""
    return await chat_service.chat(request)


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
    summary="List Conversations",
    description="List conversations owned by the authenticated user.",
    responses={
        200: {"description": "Conversation list returned."},
        401: {"description": "Authentication required."},
    },
)
async def list_conversations_endpoint(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of conversations to return.",
    ),
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
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
    summary="Create Conversation",
    description="Create a new conversation for the authenticated user.",
    responses={
        201: {"description": "Conversation created."},
        401: {"description": "Authentication required."},
        422: {"description": "Invalid conversation payload."},
    },
)
async def create_conversation_endpoint(
    payload: ConversationCreate = Body(
        description="Conversation creation payload containing an optional title."
    ),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationResponse:
    """Create a conversation for the authenticated user."""
    return await chat_service.create_conversation(
        user_id=current_user.id,
        title=payload.title,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get Conversation",
    description="Retrieve a single conversation owned by the authenticated user.",
    responses={
        200: {"description": "Conversation returned."},
        401: {"description": "Authentication required."},
        404: {"description": "Conversation not found."},
    },
)
async def get_conversation_endpoint(
    conversation_id: UUID = Path(description="Conversation identifier."),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationResponse:
    """Return one conversation owned by the authenticated user."""
    return await chat_service.get_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
    )


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Rename Conversation",
    description="Update the title of a conversation owned by the current user.",
    responses={
        200: {"description": "Conversation title updated."},
        401: {"description": "Authentication required."},
        404: {"description": "Conversation not found."},
    },
)
async def rename_conversation_endpoint(
    conversation_id: UUID = Path(description="Conversation identifier."),
    payload: ConversationUpdate = Body(
        description="Conversation update payload containing the new title."
    ),
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
    summary="Delete Conversation",
    description="Delete a conversation and its messages for the authenticated user.",
    responses={
        204: {"description": "Conversation deleted."},
        401: {"description": "Authentication required."},
        404: {"description": "Conversation not found."},
    },
)
async def delete_conversation_endpoint(
    conversation_id: UUID = Path(description="Conversation identifier."),
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
    summary="List Conversation Messages",
    description="List messages for a conversation owned by the authenticated user.",
    responses={
        200: {"description": "Message list returned."},
        401: {"description": "Authentication required."},
        404: {"description": "Conversation not found."},
    },
)
async def list_messages_endpoint(
    conversation_id: UUID = Path(description="Conversation identifier."),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of messages to return.",
    ),
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
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
    summary="Send Conversation Message",
    description=(
        "Store a user message and generate a persisted assistant response for "
        "the same conversation."
    ),
    responses={
        201: {"description": "User and assistant messages created."},
        401: {"description": "Authentication required."},
        404: {"description": "Conversation not found."},
    },
)
async def send_message_endpoint(
    conversation_id: UUID = Path(description="Conversation identifier."),
    payload: MessageCreate = Body(description="User message payload."),
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
