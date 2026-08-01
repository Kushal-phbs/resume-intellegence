"""Provider abstraction for chat conversation replies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract provider for conversation assistant replies."""

    @abstractmethod
    async def generate_reply(
        self,
        *,
        user_message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> tuple[str, dict[str, int]]:
        """Generate assistant content with optional token usage metadata."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return provider readiness status for liveness checks."""
        ...
