"""Notification request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    """Public notification payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Notification identifier.")
    user_id: UUID = Field(description="Owner user identifier.")
    title: str = Field(description="Short notification title.")
    message: str = Field(description="Notification body text.")
    type: str = Field(description="Notification type classifier.")
    priority: Literal["low", "medium", "high", "critical"] = Field(
        description="Priority used for sorting and urgency display."
    )
    is_read: bool = Field(description="Whether the notification was marked as read.")
    action_url: str | None = Field(
        default=None,
        description="Optional URL for a related action in the client.",
    )
    metadata_json: dict[str, object] = Field(
        default_factory=dict,
        description="Arbitrary structured metadata for client behavior.",
    )
    created_at: datetime = Field(description="Notification creation timestamp.")
    updated_at: datetime = Field(description="Last notification update timestamp.")


class NotificationCreate(BaseModel):
    """Payload for creating a notification."""

    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=1024)
    type: str = Field(min_length=1, max_length=64)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    action_url: str | None = Field(default=None, max_length=512)
    metadata_json: dict[str, object] = Field(default_factory=dict)


class NotificationUpdate(BaseModel):
    """Payload for notification updates."""

    is_read: bool = Field(description="Desired read-state for the notification.")


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""

    items: list[NotificationResponse] = Field(default_factory=list)
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class UnreadNotificationCount(BaseModel):
    """Unread notification count payload."""

    unread_count: int = Field(ge=0)
