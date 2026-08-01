"""Notification API endpoints."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response, status

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


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List Notifications",
    description="List notifications owned by the authenticated user.",
    responses={
        200: {"description": "Notification list returned."},
        401: {"description": "Authentication required."},
    },
)
async def list_notifications_endpoint(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of notifications to return.",
    ),
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
    order: Literal["asc", "desc"] = Query(
        default="desc",
        description="Sort direction by creation timestamp.",
    ),
    only_unread: bool = Query(
        default=False,
        description="When true, return only unread notifications.",
    ),
    priority: Literal["low", "medium", "high", "critical"] | None = Query(
        default=None,
        description="Optional priority filter.",
    ),
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


@router.get(
    "/unread-count",
    response_model=UnreadNotificationCount,
    summary="Get Unread Notification Count",
    description="Return the number of unread notifications for the current user.",
    responses={
        200: {"description": "Unread count returned."},
        401: {"description": "Authentication required."},
    },
)
async def unread_notification_count_endpoint(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> UnreadNotificationCount:
    """Return unread notification count for the authenticated user."""
    count = await notification_service.count_unread(user_id=current_user.id)
    return UnreadNotificationCount(unread_count=count)


@router.patch(
    "/read-all",
    response_model=UnreadNotificationCount,
    summary="Mark All Notifications Read",
    description="Mark all notifications as read and return updated unread count.",
    responses={
        200: {"description": "Notifications marked as read."},
        401: {"description": "Authentication required."},
    },
)
async def mark_all_notifications_read_endpoint(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> UnreadNotificationCount:
    """Mark all notifications as read for the authenticated user."""
    await notification_service.mark_all_read(user_id=current_user.id)
    count = await notification_service.count_unread(user_id=current_user.id)
    return UnreadNotificationCount(unread_count=count)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark Notification Read",
    description="Mark a single notification as read.",
    responses={
        200: {"description": "Notification updated."},
        401: {"description": "Authentication required."},
        404: {"description": "Notification not found."},
    },
)
async def mark_notification_read_endpoint(
    notification_id: UUID = Path(description="Notification identifier."),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Mark one notification as read."""
    return await notification_service.mark_read(
        user_id=current_user.id,
        notification_id=notification_id,
    )


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Notification",
    description="Delete a single notification owned by the authenticated user.",
    responses={
        204: {"description": "Notification deleted."},
        401: {"description": "Authentication required."},
        404: {"description": "Notification not found."},
    },
)
async def delete_notification_endpoint(
    notification_id: UUID = Path(description="Notification identifier."),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> Response:
    """Delete one notification."""
    await notification_service.delete_notification(
        user_id=current_user.id,
        notification_id=notification_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
