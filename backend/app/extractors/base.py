"""Text extraction abstractions for resume analysis."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TextExtractor(ABC):
    """Abstract text extractor used to normalize uploaded resume content.

    Implementations convert raw uploaded file bytes into plain text suitable
    for LLM processing.
    """

    @abstractmethod
    def extract(self, content: bytes) -> str:
        """Extract text from raw file bytes."""
        raise NotImplementedError
