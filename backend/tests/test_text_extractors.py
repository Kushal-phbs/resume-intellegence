from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

import pytest

from app.core.exceptions import UnsupportedFileTypeException, ValidationException
from app.extractors.docx import DOCXExtractor
from app.extractors.factory import TextExtractorFactory
from app.extractors.pdf import PDFExtractor
from app.extractors.txt import TXTExtractor


def test_txt_extractor_decodes_text() -> None:
    extractor = TXTExtractor()

    assert extractor.extract(b"  Hello Resume  ") == "Hello Resume"


def test_txt_extractor_rejects_invalid_encoding() -> None:
    extractor = TXTExtractor()

    with pytest.raises(ValidationException):
        extractor.extract(b"\xff\xfe")


def test_docx_extractor_reads_text() -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            (
                "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
                "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
                "<w:body><w:p><w:r><w:t>Hello Resume</w:t></w:r></w:p></w:body>"
                "</w:document>"
            ),
        )

    extractor = DOCXExtractor()

    assert extractor.extract(buffer.getvalue()) == "Hello Resume"


def test_docx_extractor_rejects_invalid_content() -> None:
    extractor = DOCXExtractor()

    with pytest.raises(ValidationException):
        extractor.extract(b"not-a-docx")


def test_pdf_extractor_reads_text(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Page:
        def extract_text(self) -> str:
            return "Hello Resume"

    class _Reader:
        def __init__(self, _stream: object) -> None:
            self.pages = [_Page()]

    monkeypatch.setattr("app.extractors.pdf.PdfReader", _Reader)

    extractor = PDFExtractor()

    assert extractor.extract(b"%PDF-1.4") == "Hello Resume"


def test_pdf_extractor_rejects_invalid_content(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Reader:
        def __init__(self, _stream: object) -> None:
            self.pages = []

    monkeypatch.setattr("app.extractors.pdf.PdfReader", _Reader)

    extractor = PDFExtractor()

    with pytest.raises(ValidationException):
        extractor.extract(b"%PDF-1.4")


def test_text_extractor_factory_selects_extractors() -> None:
    factory = TextExtractorFactory()

    assert factory.get_extractor("resume.txt").__class__ is TXTExtractor
    assert factory.get_extractor("resume.docx").__class__ is DOCXExtractor
    assert factory.get_extractor("resume.pdf").__class__ is PDFExtractor


def test_text_extractor_factory_rejects_unsupported_type() -> None:
    factory = TextExtractorFactory()

    with pytest.raises(UnsupportedFileTypeException):
        factory.get_extractor("resume.exe")
