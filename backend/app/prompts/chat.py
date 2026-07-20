"""Chat prompt implementations."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class ChatPrompt(BasePrompt):
    """Prompt builder for chat-based LLM interactions."""

    def build(self, prompt: str) -> str:
        """Return the chat prompt text unchanged for now."""
        return prompt
