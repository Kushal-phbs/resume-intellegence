from app.llm.models import LLMResponse


def test_llm_response_metadata_defaults_to_none() -> None:
    response = LLMResponse(content="hello")

    assert response.content == "hello"
    assert response.model is None
    assert response.provider is None
    assert response.input_tokens is None
    assert response.output_tokens is None
    assert response.total_tokens is None
    assert response.latency_ms is None
    assert response.finish_reason is None


def test_llm_response_accepts_optional_metadata_fields() -> None:
    response = LLMResponse(
        content="hello",
        model="test-model",
        provider="groq",
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        latency_ms=123.4,
        finish_reason="stop",
    )

    assert response.model == "test-model"
    assert response.provider == "groq"
    assert response.input_tokens == 10
    assert response.output_tokens == 20
    assert response.total_tokens == 30
    assert response.latency_ms == 123.4
    assert response.finish_reason == "stop"
