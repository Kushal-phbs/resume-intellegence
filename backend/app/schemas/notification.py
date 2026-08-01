"""Notification request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    """Public notification payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    message: str
    type: str
    priority: Literal["low", "medium", "high", "critical"]
    is_read: bool
    action_url: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


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

    is_read: bool


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""

    items: list[NotificationResponse] = Field(default_factory=list)
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class UnreadNotificationCount(BaseModel):
    """Unread notification count payload."""

    unread_count: int = Field(ge=0)
