"""Configuration objects for LLM providers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMConfig:
    """Immutable configuration for an LLM provider."""

    provider: str
    api_key: str
    model: str
    timeout: float = 30.0
    max_retries: int = 2
