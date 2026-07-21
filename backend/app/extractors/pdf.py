"""PDF resume extractor."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from app.core.exceptions import ValidationException
from app.extractors.base import TextExtractor


class PDFExtractor(TextExtractor):
    """Extract text from PDF resume files."""

    def extract(self, content: bytes) -> str:
        """Extract visible text from a PDF file using pypdf."""
        try:
            reader = PdfReader(BytesIO(content))
        except Exception as exc:  # pragma: no cover - defensive parser guard
            raise ValidationException("Unable to parse PDF resume content") from exc

        pages = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text.strip())

        text = "\n".join(pages).strip()
        if text:
            return text
        raise ValidationException("Unable to extract text from PDF resume")
