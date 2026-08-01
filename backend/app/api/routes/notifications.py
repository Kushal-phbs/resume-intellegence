"""Notification API endpoints."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies.auth import get_current_user
from app.dependencies.notification import get_notification_service
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadNotificationCount,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    order: Literal["asc", "desc"] = Query(default="desc"),
    only_unread: bool = Query(default=False),
    priority: Literal["low", "medium", "high", "critical"] | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    """List notifications for the authenticated user."""
    return await notification_service.get_notifications(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        order=order,
        only_unread=only_unread,
        priority=priority,
    )


@router.get("/unread-count", response_model=UnreadNotificationCount)
async def unread_notification_count_endpoint(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> UnreadNotificationCount:
    """Return unread notification count for the authenticated user."""
    count = await notification_service.count_unread(user_id=current_user.id)
    return UnreadNotificationCount(unread_count=count)


@router.patch("/read-all", response_model=UnreadNotificationCount)
async def mark_all_notifications_read_endpoint(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> UnreadNotificationCount:
    """Mark all notifications as read for the authenticated user."""
    await notification_service.mark_all_read(user_id=current_user.id)
    count = await notification_service.count_unread(user_id=current_user.id)
    return UnreadNotificationCount(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read_endpoint(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Mark one notification as read."""
    return await notification_service.mark_read(
        user_id=current_user.id,
        notification_id=notification_id,
    )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_endpoint(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> Response:
    """Delete one notification."""
    await notification_service.delete_notification(
        user_id=current_user.id,
        notification_id=notification_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
