from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.notifications import router as notifications_router
from app.core.exceptions import ResourceNotFoundException
from app.core.handlers import register_exception_handlers
from app.dependencies.auth import get_current_user
from app.dependencies.notification import get_notification_service


class _NotificationServiceStub:
    def __init__(self, owner_id):
        self.owner_id = owner_id
        self.items = [
            {
                "id": str(uuid4()),
                "user_id": str(owner_id),
                "title": "Resume uploaded",
                "message": "Done",
                "type": "resume_uploaded",
                "priority": "medium",
                "is_read": False,
                "action_url": "/resumes/1",
                "metadata_json": {},
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        ]

    async def get_notifications(
        self,
        *,
        user_id,
        limit,
        offset,
        order,
        only_unread,
        priority,
    ):
        _ = (limit, offset, order, only_unread, priority)
        self._assert_owner(user_id)
        return {
            "items": self.items,
            "total": 1,
            "limit": 20,
            "offset": 0,
        }

    async def count_unread(self, *, user_id):
        self._assert_owner(user_id)
        return 1

    async def mark_read(self, *, user_id, notification_id):
        _ = notification_id
        self._assert_owner(user_id)
        return self.items[0]

    async def mark_all_read(self, *, user_id):
        self._assert_owner(user_id)
        return 1

    async def delete_notification(self, *, user_id, notification_id):
        _ = notification_id
        self._assert_owner(user_id)

    def _assert_owner(self, user_id):
        if user_id != self.owner_id:
            raise ResourceNotFoundException("Notification not found")


def _build_app(service_stub: _NotificationServiceStub, current_user_id) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(notifications_router)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=current_user_id
    )
    app.dependency_overrides[get_notification_service] = lambda: service_stub
    return app


def test_list_notifications_supports_filters_and_pagination() -> None:
    user_id = uuid4()
    client = TestClient(_build_app(_NotificationServiceStub(user_id), user_id))

    response = client.get(
        "/notifications?limit=20&offset=0&order=desc&only_unread=true&priority=medium"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["type"] == "resume_uploaded"


def test_get_unread_notification_count() -> None:
    user_id = uuid4()
    client = TestClient(_build_app(_NotificationServiceStub(user_id), user_id))

    response = client.get("/notifications/unread-count")

    assert response.status_code == 200
    assert response.json()["unread_count"] == 1


def test_mark_notification_read() -> None:
    user_id = uuid4()
    client = TestClient(_build_app(_NotificationServiceStub(user_id), user_id))

    response = client.patch(f"/notifications/{uuid4()}/read")

    assert response.status_code == 200
    assert response.json()["is_read"] is False


def test_mark_all_notifications_read() -> None:
    user_id = uuid4()
    client = TestClient(_build_app(_NotificationServiceStub(user_id), user_id))

    response = client.patch("/notifications/read-all")

    assert response.status_code == 200
    assert response.json()["unread_count"] == 1


def test_delete_notification() -> None:
    user_id = uuid4()
    client = TestClient(_build_app(_NotificationServiceStub(user_id), user_id))

    response = client.delete(f"/notifications/{uuid4()}")

    assert response.status_code == 204
