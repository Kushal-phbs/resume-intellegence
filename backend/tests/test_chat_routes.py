from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.chat import router as chat_router
from app.core.handlers import register_exception_handlers
from app.dependencies.auth import get_current_user
from app.dependencies.chat import get_chat_service


class _ChatServiceStub:
    def __init__(self, owner_id):
        self.owner_id = owner_id
        self.conversation_id = uuid4()

    async def chat(self, request):
        return {
            "content": f"echo:{request.prompt}",
            "model": "stub-model",
            "provider": "stub-provider",
            "input_tokens": 1,
            "output_tokens": 1,
            "total_tokens": 2,
            "latency_ms": 10.0,
            "finish_reason": "stop",
        }

    async def list_conversations(self, *, user_id, limit, offset):
        _ = (user_id, limit, offset)
        now = datetime.now(UTC)
        return [
            {
                "id": str(self.conversation_id),
                "user_id": str(self.owner_id),
                "title": "Prep",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        ]

    async def create_conversation(self, *, user_id, title):
        _ = user_id
        now = datetime.now(UTC)
        return {
            "id": str(self.conversation_id),
            "user_id": str(self.owner_id),
            "title": title,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

    async def get_conversation(self, *, user_id, conversation_id):
        _ = (user_id, conversation_id)
        now = datetime.now(UTC)
        return {
            "id": str(self.conversation_id),
            "user_id": str(self.owner_id),
            "title": "Prep",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

    async def rename_conversation(self, *, user_id, conversation_id, title):
        _ = (user_id, conversation_id)
        now = datetime.now(UTC)
        return {
            "id": str(self.conversation_id),
            "user_id": str(self.owner_id),
            "title": title,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

    async def delete_conversation(self, *, user_id, conversation_id):
        _ = (user_id, conversation_id)

    async def list_messages(self, *, user_id, conversation_id, limit, offset):
        _ = (user_id, conversation_id, limit, offset)
        now = datetime.now(UTC)
        return [
            {
                "id": str(uuid4()),
                "conversation_id": str(self.conversation_id),
                "role": "user",
                "content": "Hi",
                "token_count": 1,
                "created_at": now.isoformat(),
            }
        ]

    async def send_message(self, *, user_id, conversation_id, content):
        _ = (user_id, conversation_id, content)
        now = datetime.now(UTC)
        conversation = {
            "id": str(self.conversation_id),
            "user_id": str(self.owner_id),
            "title": "Prep",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        user_message = {
            "id": str(uuid4()),
            "conversation_id": str(self.conversation_id),
            "role": "user",
            "content": "Hello",
            "token_count": 1,
            "created_at": now.isoformat(),
        }
        assistant_message = {
            "id": str(uuid4()),
            "conversation_id": str(self.conversation_id),
            "role": "assistant",
            "content": "Hi there",
            "token_count": 2,
            "created_at": now.isoformat(),
        }
        return conversation, user_message, assistant_message, {"total_tokens": 3}, 0.01


def _build_app(service_stub: _ChatServiceStub, current_user_id) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(chat_router)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=current_user_id
    )
    app.dependency_overrides[get_chat_service] = lambda: service_stub
    return app


def test_legacy_chat_endpoint_preserved() -> None:
    user_id = uuid4()
    client = TestClient(_build_app(_ChatServiceStub(user_id), user_id))

    response = client.post("/chat/", json={"prompt": "hello"})

    assert response.status_code == 200
    assert response.json()["content"] == "echo:hello"


def test_chat_conversation_crud_and_messages_routes() -> None:
    user_id = uuid4()
    client = TestClient(_build_app(_ChatServiceStub(user_id), user_id))

    listed = client.get("/chat/conversations?limit=10&offset=0")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    created = client.post("/chat/conversations", json={"title": "My Plan"})
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    fetched = client.get(f"/chat/conversations/{conversation_id}")
    assert fetched.status_code == 200

    renamed = client.patch(
        f"/chat/conversations/{conversation_id}",
        json={"title": "Renamed"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Renamed"

    messages = client.get(f"/chat/conversations/{conversation_id}/messages")
    assert messages.status_code == 200
    assert messages.json()[0]["role"] == "user"

    sent = client.post(
        f"/chat/conversations/{conversation_id}/messages",
        json={"content": "hello"},
    )
    assert sent.status_code == 201
    assert sent.json()["assistant_message"]["role"] == "assistant"

    deleted = client.delete(f"/chat/conversations/{conversation_id}")
    assert deleted.status_code == 204


def test_chat_validation_rejects_blank_or_too_long_payloads() -> None:
    user_id = uuid4()
    client = TestClient(_build_app(_ChatServiceStub(user_id), user_id))

    blank_title = client.post("/chat/conversations", json={"title": "   "})
    assert blank_title.status_code == 422

    blank_message = client.post(
        f"/chat/conversations/{uuid4()}/messages",
        json={"content": "   "},
    )
    assert blank_message.status_code == 422

    too_long_message = client.post(
        f"/chat/conversations/{uuid4()}/messages",
        json={"content": "a" * 4001},
    )
    assert too_long_message.status_code == 422
