"""Factory for selecting resume text extractors."""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import UnsupportedFileTypeException
from app.extractors.base import TextExtractor
from app.extractors.docx import DOCXExtractor
from app.extractors.pdf import PDFExtractor
from app.extractors.txt import TXTExtractor


class TextExtractorFactory:
    """Select a text extractor based on a resume file's extension."""

    def get_extractor(self, file_path: str) -> TextExtractor:
        """Return the extractor implementation for the given file path."""
        suffix = Path(file_path).suffix.lower()
        if suffix == ".txt":
            return TXTExtractor()
        if suffix == ".docx":
            return DOCXExtractor()
        if suffix == ".pdf":
            return PDFExtractor()
        raise UnsupportedFileTypeException(
            f"Unsupported resume content type: {suffix or 'unknown'}"
        )
