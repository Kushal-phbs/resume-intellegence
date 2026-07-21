"""Plain-text resume extractor."""

from __future__ import annotations

from app.core.exceptions import ValidationException
from app.extractors.base import TextExtractor


class TXTExtractor(TextExtractor):
    """Extract text from UTF-8 encoded plain-text resumes."""

    def extract(self, content: bytes) -> str:
        """Decode and normalize plain-text resume bytes."""
        try:
            return content.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValidationException("Unable to decode resume text") from exc
