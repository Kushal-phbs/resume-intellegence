"""Provider-agnostic prompt abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BasePrompt(ABC):
    """Abstract base class for building prompt text."""

    @abstractmethod
    def build(self, **kwargs: object) -> str:
        """Build and return the prompt text."""
        raise NotImplementedError
