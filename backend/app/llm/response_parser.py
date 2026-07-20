"""Provider-agnostic response parsing utilities for LLM output."""

from __future__ import annotations

import re

__all__ = ["ResponseParser"]


class ResponseParser:
    """Parse and clean raw LLM response text."""

    @staticmethod
    def clean(text: str | None) -> str:
        """Clean the raw text returned by an LLM provider.

        This removes any <think>...</think> blocks, trims whitespace, and
        collapses repeated blank lines.
        """
        if not text:
            return ""

        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        cleaned = cleaned.strip()
        cleaned = re.sub(r"(?:\r?\n){3,}", "\n\n", cleaned)
        return cleaned
