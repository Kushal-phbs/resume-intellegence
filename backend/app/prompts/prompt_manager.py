"""Central point for prompt object creation."""

from __future__ import annotations

from app.prompts.chat import ChatPrompt


class PromptManager:
    """Factory for prompt objects used by the application."""

    @staticmethod
    def get_chat_prompt() -> ChatPrompt:
        """Return a new ChatPrompt instance."""
        return ChatPrompt()
