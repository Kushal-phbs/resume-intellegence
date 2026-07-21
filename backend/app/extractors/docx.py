"""DOCX resume extractor."""

from __future__ import annotations

from io import BytesIO
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from app.core.exceptions import ValidationException
from app.extractors.base import TextExtractor


class DOCXExtractor(TextExtractor):
    """Extract text from Microsoft Word DOCX resume files."""

    def extract(self, content: bytes) -> str:
        """Extract text from a DOCX file by reading the document XML."""
        try:
            with ZipFile(BytesIO(content)) as archive:
                document = archive.read("word/document.xml")
        except (BadZipFile, KeyError, OSError, UnicodeDecodeError, ValueError) as exc:
            raise ValidationException(
                "Unable to extract text from DOCX resume"
            ) from exc

        try:
            root = ElementTree.fromstring(document)
        except ElementTree.ParseError as exc:
            raise ValidationException("Unable to parse DOCX resume content") from exc

        namespace = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        }
        texts = [
            node.text.strip()
            for node in root.findall(".//w:t", namespace)
            if node.text and node.text.strip()
        ]
        return "\n".join(texts).strip()
