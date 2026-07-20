"""Pydantic models for LLM request and response payloads."""

from __future__ import annotations

from pydantic import BaseModel


class LLMRequest(BaseModel):
    """Request payload for an LLM generation call."""

    prompt: str
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1024


class LLMResponse(BaseModel):
    """Response payload returned after generating text from an LLM.

    The model and provider fields are included as optional metadata, and
    token usage and latency fields remain None when unavailable.
    """

    content: str
    model: str | None = None
    provider: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float | None = None
    finish_reason: str | None = None
