import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ResourceNotFoundException
from app.llm.models import LLMRequest, LLMResponse
from app.services.chat_service import ChatService


async def _collect_chunks(stream) -> list[str]:
    chunks: list[str] = []
    async for chunk in stream:
        chunks.append(chunk)
    return chunks


def test_chat_service_delegates_to_provider() -> None:
    """Verify ChatService forwards requests to the configured provider."""
    provider = AsyncMock()
    expected = LLMResponse(content="result", model="test-model", provider="groq")
    provider.generate.return_value = expected

    service = ChatService(provider)
    request = LLMRequest(prompt="hello")

    result = asyncio.run(service.chat(request))

    provider.generate.assert_awaited_once_with(request)
    assert result == expected


def test_chat_service_propagates_provider_error() -> None:
    """Verify ChatService does not swallow provider exceptions."""
    provider = AsyncMock()
    provider.generate.side_effect = RuntimeError("provider failure")

    service = ChatService(provider)
    request = LLMRequest(prompt="hello")

    with pytest.raises(RuntimeError, match="provider failure"):
        asyncio.run(service.chat(request))


def test_create_and_list_conversations() -> None:
    provider = AsyncMock()
    conversation_repository = AsyncMock()
    now = datetime.now(UTC)
    user_id = uuid4()
    conversation = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        title="Career Planning",
        created_at=now,
        updated_at=now,
    )
    conversation_repository.create.return_value = conversation
    conversation_repository.list_by_user.return_value = [conversation]

    service = ChatService(
        provider,
        conversation_repository=conversation_repository,
    )

    created = asyncio.run(
        service.create_conversation(user_id=user_id, title="Career Planning")
    )
    listed = asyncio.run(
        service.list_conversations(user_id=user_id, limit=50, offset=0)
    )

    assert created.id == conversation.id
    assert listed[0].title == "Career Planning"


def test_send_message_persists_user_and_assistant_messages() -> None:
    provider = AsyncMock()
    ai_provider = AsyncMock()
    ai_provider.generate_reply.return_value = (
        "Focus on quantified impact.",
        {
            "input_tokens": 8,
            "output_tokens": 9,
            "total_tokens": 17,
        },
    )
    conversation_repository = AsyncMock()
    message_repository = AsyncMock()
    resume_repository = AsyncMock()
    resume_analysis_repository = AsyncMock()
    job_analysis_repository = AsyncMock()
    dashboard_repository = AsyncMock()

    user_id = uuid4()
    conversation_id = uuid4()
    now = datetime.now(UTC)

    conversation_repository.get.return_value = SimpleNamespace(
        id=conversation_id,
        user_id=user_id,
        title="Interview Prep",
        created_at=now,
        updated_at=now,
    )
    user_message = SimpleNamespace(
        id=uuid4(),
        conversation_id=conversation_id,
        role="user",
        content="Help me improve my summary",
        token_count=8,
        created_at=now,
    )
    assistant_message = SimpleNamespace(
        id=uuid4(),
        conversation_id=conversation_id,
        role="assistant",
        content="Focus on quantified impact.",
        token_count=9,
        created_at=now,
    )
    message_repository.create.side_effect = [user_message, assistant_message]
    message_repository.list_messages.return_value = [user_message]

    latest_resume = SimpleNamespace(
        id=uuid4(),
        title="Backend Resume",
        is_primary=True,
        created_at=now,
    )
    resume_repository.list_by_user.return_value = [latest_resume]
    resume_repository.get_latest_version.return_value = SimpleNamespace(
        id=uuid4(),
        version_number=3,
    )
    resume_analysis_repository.get_latest_completed.return_value = SimpleNamespace(
        id=uuid4(),
        resume_score=90,
        ats_score=88,
        strengths=["Strong backend experience"],
        weaknesses=[],
    )
    job_analysis_repository.list_by_user.return_value = [
        SimpleNamespace(
            id=uuid4(),
            match_score=84,
            ats_match_score=80,
            summary="Good match",
        )
    ]
    dashboard_repository.calculate_metrics.return_value = {"total_resumes": 1}

    service = ChatService(
        provider,
        ai_provider=ai_provider,
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        resume_repository=resume_repository,
        resume_analysis_repository=resume_analysis_repository,
        job_analysis_repository=job_analysis_repository,
        dashboard_repository=dashboard_repository,
    )

    (
        conversation,
        created_user,
        created_assistant,
        token_usage,
        processing_time,
    ) = asyncio.run(
        service.send_message(
            user_id=user_id,
            conversation_id=conversation_id,
            content="Help me improve my summary",
        )
    )

    assert conversation.id == conversation_id
    assert created_user.role == "user"
    assert created_assistant.role == "assistant"
    assert token_usage["total_tokens"] >= 1
    assert processing_time >= 0


def test_send_message_uses_latest_15_messages_for_rolling_context() -> None:
    provider = AsyncMock()
    ai_provider = AsyncMock()
    ai_provider.generate_reply.return_value = (
        "assistant reply",
        {
            "input_tokens": 1,
            "output_tokens": 2,
            "total_tokens": 3,
        },
    )
    conversation_repository = AsyncMock()
    message_repository = AsyncMock()
    resume_repository = AsyncMock()
    resume_analysis_repository = AsyncMock()
    job_analysis_repository = AsyncMock()
    dashboard_repository = AsyncMock()

    user_id = uuid4()
    conversation_id = uuid4()
    now = datetime.now(UTC)

    conversation_repository.get.return_value = SimpleNamespace(
        id=conversation_id,
        user_id=user_id,
        title="Interview Prep",
        created_at=now,
        updated_at=now,
    )

    # First create() persists user message, second persists assistant message.
    message_repository.create.side_effect = [
        SimpleNamespace(
            id=uuid4(),
            conversation_id=conversation_id,
            role="user",
            content="latest question",
            token_count=1,
            created_at=now,
        ),
        SimpleNamespace(
            id=uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content="assistant reply",
            token_count=2,
            created_at=now,
        ),
    ]

    # 30 chronological messages; window should keep indices 15..29.
    message_repository.list_messages.return_value = [
        SimpleNamespace(role="user", content=f"m{i}") for i in range(30)
    ]

    resume_repository.list_by_user.return_value = []
    job_analysis_repository.list_by_user.return_value = []
    dashboard_repository.calculate_metrics.return_value = {}

    service = ChatService(
        provider,
        ai_provider=ai_provider,
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        resume_repository=resume_repository,
        resume_analysis_repository=resume_analysis_repository,
        job_analysis_repository=job_analysis_repository,
        dashboard_repository=dashboard_repository,
    )

    asyncio.run(
        service.send_message(
            user_id=user_id,
            conversation_id=conversation_id,
            content="latest question",
        )
    )

    called_history = ai_provider.generate_reply.await_args.kwargs["history"]
    assert called_history[0]["role"] == "system"
    assert len(called_history) == 16
    assert called_history[1]["content"] == "m15"
    assert called_history[-1]["content"] == "m29"


def test_send_message_prepends_summary_when_history_exceeds_40() -> None:
    provider = AsyncMock()
    ai_provider = AsyncMock()
    ai_provider.generate_reply.side_effect = [
        (
            "summary text",
            {
                "input_tokens": 20,
                "output_tokens": 10,
                "total_tokens": 30,
            },
        ),
        (
            "assistant reply",
            {
                "input_tokens": 1,
                "output_tokens": 2,
                "total_tokens": 3,
            },
        ),
    ]
    conversation_repository = AsyncMock()
    message_repository = AsyncMock()
    resume_repository = AsyncMock()
    resume_analysis_repository = AsyncMock()
    job_analysis_repository = AsyncMock()
    dashboard_repository = AsyncMock()

    user_id = uuid4()
    conversation_id = uuid4()
    now = datetime.now(UTC)

    conversation_repository.get.return_value = SimpleNamespace(
        id=conversation_id,
        user_id=user_id,
        title="Interview Prep",
        created_at=now,
        updated_at=now,
    )

    message_repository.create.side_effect = [
        SimpleNamespace(
            id=uuid4(),
            conversation_id=conversation_id,
            role="user",
            content="latest question",
            token_count=1,
            created_at=now,
        ),
        SimpleNamespace(
            id=uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content="assistant reply",
            token_count=2,
            created_at=now,
        ),
    ]

    message_repository.list_messages.return_value = [
        SimpleNamespace(role="user", content=f"m{i}") for i in range(45)
    ]

    resume_repository.list_by_user.return_value = []
    job_analysis_repository.list_by_user.return_value = []
    dashboard_repository.calculate_metrics.return_value = {}

    service = ChatService(
        provider,
        ai_provider=ai_provider,
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        resume_repository=resume_repository,
        resume_analysis_repository=resume_analysis_repository,
        job_analysis_repository=job_analysis_repository,
        dashboard_repository=dashboard_repository,
    )

    asyncio.run(
        service.send_message(
            user_id=user_id,
            conversation_id=conversation_id,
            content="latest question",
        )
    )

    assert ai_provider.generate_reply.await_count == 2

    summary_call = ai_provider.generate_reply.await_args_list[0].kwargs
    assert "Summarize the prior conversation" in summary_call["user_message"]
    assert len(summary_call["history"]) == 30
    assert summary_call["history"][0]["content"] == "m0"
    assert summary_call["history"][-1]["content"] == "m29"

    main_call = ai_provider.generate_reply.await_args_list[1].kwargs
    main_history = main_call["history"]
    assert main_history[0]["role"] == "system"
    assert main_history[1]["role"] == "system"
    assert main_history[1]["content"] == "Conversation summary: summary text"
    assert len(main_history) == 17
    assert main_history[2]["content"] == "m30"
    assert main_history[-1]["content"] == "m44"


def test_send_message_skips_summary_when_summary_generation_fails() -> None:
    provider = AsyncMock()
    ai_provider = AsyncMock()
    ai_provider.generate_reply.side_effect = [
        RuntimeError("summary failed"),
        (
            "assistant reply",
            {
                "input_tokens": 1,
                "output_tokens": 2,
                "total_tokens": 3,
            },
        ),
    ]
    conversation_repository = AsyncMock()
    message_repository = AsyncMock()
    resume_repository = AsyncMock()
    resume_analysis_repository = AsyncMock()
    job_analysis_repository = AsyncMock()
    dashboard_repository = AsyncMock()

    user_id = uuid4()
    conversation_id = uuid4()
    now = datetime.now(UTC)

    conversation_repository.get.return_value = SimpleNamespace(
        id=conversation_id,
        user_id=user_id,
        title="Interview Prep",
        created_at=now,
        updated_at=now,
    )

    message_repository.create.side_effect = [
        SimpleNamespace(
            id=uuid4(),
            conversation_id=conversation_id,
            role="user",
            content="latest question",
            token_count=1,
            created_at=now,
        ),
        SimpleNamespace(
            id=uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content="assistant reply",
            token_count=2,
            created_at=now,
        ),
    ]

    message_repository.list_messages.return_value = [
        SimpleNamespace(role="user", content=f"m{i}") for i in range(45)
    ]

    resume_repository.list_by_user.return_value = []
    job_analysis_repository.list_by_user.return_value = []
    dashboard_repository.calculate_metrics.return_value = {}

    service = ChatService(
        provider,
        ai_provider=ai_provider,
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        resume_repository=resume_repository,
        resume_analysis_repository=resume_analysis_repository,
        job_analysis_repository=job_analysis_repository,
        dashboard_repository=dashboard_repository,
    )

    asyncio.run(
        service.send_message(
            user_id=user_id,
            conversation_id=conversation_id,
            content="latest question",
        )
    )

    main_call = ai_provider.generate_reply.await_args_list[1].kwargs
    main_history = main_call["history"]
    assert main_history[0]["role"] == "system"
    assert len(main_history) == 16
    assert main_history[1]["content"] == "m30"


def test_send_message_raises_for_non_owner_conversation() -> None:
    provider = AsyncMock()
    conversation_repository = AsyncMock()
    conversation_repository.get.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        title="Foreign",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    service = ChatService(
        provider,
        conversation_repository=conversation_repository,
        message_repository=AsyncMock(),
        resume_repository=AsyncMock(),
        resume_analysis_repository=AsyncMock(),
        job_analysis_repository=AsyncMock(),
        dashboard_repository=AsyncMock(),
    )

    with pytest.raises(ResourceNotFoundException):
        asyncio.run(
            service.send_message(
                user_id=uuid4(),
                conversation_id=uuid4(),
                content="test",
            )
        )


def test_stream_reply_delegates_to_provider_stream_reply() -> None:
    class StreamingProvider:
        async def generate_reply(self, **kwargs):  # pragma: no cover
            return "unused", {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        async def stream_reply(self, **kwargs):
            self.kwargs = kwargs
            yield "part-1"
            yield "part-2"

    provider = AsyncMock()
    ai_provider = StreamingProvider()
    conversation_repository = AsyncMock()
    message_repository = AsyncMock()
    resume_repository = AsyncMock()
    resume_analysis_repository = AsyncMock()
    job_analysis_repository = AsyncMock()
    dashboard_repository = AsyncMock()

    user_id = uuid4()
    conversation_id = uuid4()
    now = datetime.now(UTC)

    conversation_repository.get.return_value = SimpleNamespace(
        id=conversation_id,
        user_id=user_id,
        title="Interview Prep",
        created_at=now,
        updated_at=now,
    )
    message_repository.list_messages.return_value = [
        SimpleNamespace(role="user", content="previous")
    ]
    resume_repository.list_by_user.return_value = []
    job_analysis_repository.list_by_user.return_value = []
    dashboard_repository.calculate_metrics.return_value = {}

    service = ChatService(
        provider,
        ai_provider=ai_provider,
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        resume_repository=resume_repository,
        resume_analysis_repository=resume_analysis_repository,
        job_analysis_repository=job_analysis_repository,
        dashboard_repository=dashboard_repository,
    )

    chunks = asyncio.run(
        _collect_chunks(
            service.stream_reply(
                user_id=user_id,
                conversation_id=conversation_id,
                content="latest question",
            )
        )
    )

    assert chunks == ["part-1", "part-2"]
    assert ai_provider.kwargs["user_message"] == "latest question"
    assert ai_provider.kwargs["history"][0]["role"] == "system"


def test_stream_reply_falls_back_to_generate_reply_when_stream_unavailable() -> None:
    class NonStreamingProvider:
        def __init__(self) -> None:
            self.called_with = None

        async def generate_reply(self, **kwargs):
            self.called_with = kwargs
            return (
                "x" * 260,
                {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
            )

    provider = AsyncMock()
    ai_provider = NonStreamingProvider()
    conversation_repository = AsyncMock()
    message_repository = AsyncMock()
    resume_repository = AsyncMock()
    resume_analysis_repository = AsyncMock()
    job_analysis_repository = AsyncMock()
    dashboard_repository = AsyncMock()

    user_id = uuid4()
    conversation_id = uuid4()
    now = datetime.now(UTC)

    conversation_repository.get.return_value = SimpleNamespace(
        id=conversation_id,
        user_id=user_id,
        title="Interview Prep",
        created_at=now,
        updated_at=now,
    )
    message_repository.list_messages.return_value = []
    resume_repository.list_by_user.return_value = []
    job_analysis_repository.list_by_user.return_value = []
    dashboard_repository.calculate_metrics.return_value = {}

    service = ChatService(
        provider,
        ai_provider=ai_provider,
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        resume_repository=resume_repository,
        resume_analysis_repository=resume_analysis_repository,
        job_analysis_repository=job_analysis_repository,
        dashboard_repository=dashboard_repository,
    )

    chunks = asyncio.run(
        _collect_chunks(
            service.stream_reply(
                user_id=user_id,
                conversation_id=conversation_id,
                content="latest question",
            )
        )
    )

    assert len(chunks) == 3
    assert "".join(chunks) == "x" * 260
    assert ai_provider.called_with is not None
    assert ai_provider.called_with["user_message"] == "latest question"
