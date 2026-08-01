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

    title: TitleText = Field(
        default="New Conversation",
        description="Optional conversation title shown in conversation lists.",
        examples=["Interview Prep"],
    )


class ConversationUpdate(BaseModel):
    """Payload to update a conversation title."""

    title: TitleText = Field(description="New conversation title.")


class ConversationResponse(BaseModel):
    """Response schema for persisted conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Conversation identifier.")
    user_id: UUID = Field(description="Owner user identifier.")
    title: str = Field(description="Conversation title.")
    created_at: datetime = Field(description="Conversation creation timestamp.")
    updated_at: datetime = Field(description="Last conversation update timestamp.")


class MessageCreate(BaseModel):
    """Payload to send a user message."""

    content: MessageText = Field(
        description="User message content sent to the assistant."
    )


class MessageResponse(BaseModel):
    """Response schema for persisted conversation messages."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Message identifier.")
    conversation_id: UUID = Field(description="Conversation identifier.")
    role: Literal["user", "assistant", "system"] = Field(
        description="Message role in the conversation timeline."
    )
    content: str = Field(description="Message text content.")
    token_count: int = Field(
        ge=0,
        description="Token usage attributed to this message when available.",
    )
    created_at: datetime = Field(description="Message creation timestamp.")


class ChatResponse(BaseModel):
    """Response schema for chat send-message endpoint."""

    conversation: ConversationResponse = Field(
        description="Conversation associated with this exchange."
    )
    user_message: MessageResponse = Field(description="Persisted user message.")
    assistant_message: MessageResponse = Field(
        description="Persisted assistant response message."
    )
    token_usage: dict[str, int] = Field(
        default_factory=dict,
        description="Aggregate token usage reported by the LLM provider.",
    )
    processing_time: float = Field(
        ge=0,
        description="Total processing time for this exchange in seconds.",
    )
