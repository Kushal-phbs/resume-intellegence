"""Conversation and message schemas for chat assistant APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

TitleText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
MessageText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=4000),
]


class ConversationCreate(BaseModel):
    """Payload to create a conversation."""

    title: TitleText = "New Conversation"


class ConversationUpdate(BaseModel):
    """Payload to update a conversation title."""

    title: TitleText


class ConversationResponse(BaseModel):
    """Response schema for persisted conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    """Payload to send a user message."""

    content: MessageText


class MessageResponse(BaseModel):
    """Response schema for persisted conversation messages."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: Literal["user", "assistant", "system"]
    content: str
    token_count: int = Field(ge=0)
    created_at: datetime


class ChatResponse(BaseModel):
    """Response schema for chat send-message endpoint."""

    conversation: ConversationResponse
    user_message: MessageResponse
    assistant_message: MessageResponse
    token_usage: dict[str, int] = Field(default_factory=dict)
    processing_time: float = Field(ge=0)
