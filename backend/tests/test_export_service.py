from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.repositories.cover_letter_repository import CoverLetterRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.resume_version_repository import ResumeVersionRepository
from app.services.export_service import ExportService
from app.storage.base import StorageProvider
from pypdf import PdfReader


class _StorageStub(StorageProvider):
    def __init__(self, download_path: Path) -> None:
        self.download_path = download_path
        self.saved: list[tuple[bytes, str]] = []

    def save(self, *, content: bytes, filename: str) -> str:
        self.saved.append((content, filename))
        return "exports/key.md"

    def read(self, storage_key: str) -> bytes:
        raise NotImplementedError

    def delete(self, storage_key: str) -> None:
        raise NotImplementedError

    def exists(self, storage_key: str) -> bool:
        raise NotImplementedError

    def get_download_path(self, storage_key: str) -> Path:
        _ = storage_key
        return self.download_path


def _build_service(
    tmp_path: Path,
) -> tuple[
    ExportService,
    AsyncMock,
    AsyncMock,
    AsyncMock,
    _StorageStub,
]:
    resume_version_repository = AsyncMock(spec=ResumeVersionRepository)
    cover_letter_repository = AsyncMock(spec=CoverLetterRepository)
    resume_repository = AsyncMock(spec=ResumeRepository)
    storage = _StorageStub(tmp_path / "exported.md")
    service = ExportService(
        resume_version_repository,
        cover_letter_repository,
        resume_repository,
        storage,
    )
    return (
        service,
        resume_version_repository,
        cover_letter_repository,
        resume_repository,
        storage,
    )


def test_export_resume_markdown_success(tmp_path: Path) -> None:
    (
        service,
        resume_versions,
        _cover_letters,
        resumes,
        storage,
    ) = _build_service(tmp_path)
    owner_id = uuid4()
    resume_id = uuid4()
    version_id = uuid4()

    resume_versions.get_by_id.return_value = SimpleNamespace(
        id=version_id,
        resume_id=resume_id,
        professional_summary="Summary",
        experience_json=[{"text": "Built APIs"}],
        skills_json=[{"name": "Python"}],
        ats_score=90,
        recommendations_json=[{"text": "Add metrics"}],
    )
    resumes.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)

    path = asyncio.run(
        service.export_resume(
            user_id=owner_id,
            version_id=version_id,
            format="md",
        )
    )

    assert path == storage.download_path
    assert storage.saved
    assert b"Tailored Resume" in storage.saved[0][0]


def test_export_resume_invalid_format_raises(tmp_path: Path) -> None:
    (
        service,
        resume_versions,
        _cover_letters,
        resumes,
        _storage,
    ) = _build_service(tmp_path)
    owner_id = uuid4()
    resume_id = uuid4()
    version_id = uuid4()

    resume_versions.get_by_id.return_value = SimpleNamespace(
        id=version_id,
        resume_id=resume_id,
        professional_summary="Summary",
        experience_json=[],
        skills_json=[],
        ats_score=75,
        recommendations_json=[],
    )
    resumes.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)

    with pytest.raises(ValidationException, match="Unsupported export format"):
        asyncio.run(
            service.export_resume(
                user_id=owner_id,
                version_id=version_id,
                format="exe",
            )
        )


def test_export_resume_missing_version_raises(tmp_path: Path) -> None:
    (
        service,
        resume_versions,
        _cover_letters,
        _resumes,
        _storage,
    ) = _build_service(tmp_path)
    resume_versions.get_by_id.return_value = None

    with pytest.raises(
        ResourceNotFoundException,
        match="Tailored resume version not found",
    ):
        asyncio.run(
            service.export_resume(
                user_id=uuid4(),
                version_id=uuid4(),
                format="md",
            )
        )


def test_export_resume_pdf_success(tmp_path: Path) -> None:
    """PDF export produces valid PDF bytes with visible text."""
    (
        service,
        resume_versions,
        _cover_letters,
        resumes,
        storage,
    ) = _build_service(tmp_path)
    owner_id = uuid4()
    resume_id = uuid4()
    version_id = uuid4()

    resume_versions.get_by_id.return_value = SimpleNamespace(
        id=version_id,
        resume_id=resume_id,
        professional_summary="Experienced Python developer.",
        experience_json=[{"text": "Built APIs at scale"}],
        skills_json=[{"name": "Python"}, {"name": "FastAPI"}],
        ats_score=92,
        recommendations_json=[{"text": "Add leadership examples"}],
    )
    resumes.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)

    path = asyncio.run(
        service.export_resume(
            user_id=owner_id,
            version_id=version_id,
            format="pdf",
        )
    )

    assert path == storage.download_path
    assert storage.saved
    raw = storage.saved[0][0]

    # 1. Valid PDF bytes
    assert raw[:5] == b"%PDF-"
    assert raw.rstrip().endswith(b"%%EOF")

    # 2. At least one page with visible text
    reader = PdfReader(BytesIO(raw))
    assert len(reader.pages) >= 1
    text = reader.pages[0].extract_text()
    assert "Tailored Resume" in text
    assert "Python" in text
    assert "FastAPI" in text


def test_export_resume_pdf_multipage(tmp_path: Path) -> None:
    """Long resume content produces multiple PDF pages."""
    (
        service,
        resume_versions,
        _cover_letters,
        resumes,
        storage,
    ) = _build_service(tmp_path)
    owner_id = uuid4()
    resume_id = uuid4()
    version_id = uuid4()

    # Generate enough content to overflow one US Letter page
    long_summary = "Paragraph. " * 200
    many_skills = [{"name": f"Skill {i}"} for i in range(100)]
    many_recs = [{"text": f"Recommendation {i}"} for i in range(50)]

    resume_versions.get_by_id.return_value = SimpleNamespace(
        id=version_id,
        resume_id=resume_id,
        professional_summary=long_summary,
        experience_json=[{"text": "Exp 1"}],
        skills_json=many_skills,
        ats_score=85,
        recommendations_json=many_recs,
    )
    resumes.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)

    asyncio.run(
        service.export_resume(
            user_id=owner_id,
            version_id=version_id,
            format="pdf",
        )
    )

    raw = storage.saved[0][0]
    reader = PdfReader(BytesIO(raw))
    assert len(reader.pages) > 1, f"Expected multiple pages, got {len(reader.pages)}"
    # Verify text is present across pages
    all_text = "".join(p.extract_text() for p in reader.pages)
    assert "Tailored Resume" in all_text
    assert "Skill 99" in all_text


def test_export_cover_letter_pdf_success(tmp_path: Path) -> None:
    """Cover letter PDF export produces valid PDF with expected text."""
    (
        service,
        _resume_versions,
        cover_letters,
        resumes,
        storage,
    ) = _build_service(tmp_path)
    owner_id = uuid4()
    resume_id = uuid4()
    cover_letter_id = uuid4()

    cover_letters.get_by_id.return_value = SimpleNamespace(
        id=cover_letter_id,
        title="Application for Software Engineer",
        greeting="Dear Hiring Manager,",
        introduction="I am writing to express my interest.",
        body="I have 5 years of experience in Python.",
        closing="Sincerely, John Doe",
        tailoring_session=SimpleNamespace(resume_id=resume_id),
    )
    resumes.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)

    path = asyncio.run(
        service.export_cover_letter(
            user_id=owner_id,
            cover_letter_id=cover_letter_id,
            format="pdf",
        )
    )

    assert path == storage.download_path
    raw = storage.saved[0][0]
    assert raw[:5] == b"%PDF-"

    reader = PdfReader(BytesIO(raw))
    assert len(reader.pages) >= 1
    text = reader.pages[0].extract_text()
    assert "Software Engineer" in text
    assert "Dear Hiring Manager" in text
    assert "John Doe" in text


def test_export_resume_docx_success(tmp_path: Path) -> None:
    """DOCX export produces a valid ZIP/OOXML document with resume text."""
    (
        service,
        resume_versions,
        _cover_letters,
        resumes,
        storage,
    ) = _build_service(tmp_path)
    owner_id = uuid4()
    resume_id = uuid4()
    version_id = uuid4()

    resume_versions.get_by_id.return_value = SimpleNamespace(
        id=version_id,
        resume_id=resume_id,
        professional_summary="Expert in data pipelines.",
        experience_json=[{"text": "Built ETL pipelines"}],
        skills_json=[{"name": "Python"}, {"name": "SQL"}],
        ats_score=88,
        recommendations_json=[{"text": "Add cloud experience"}],
    )
    resumes.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)

    asyncio.run(
        service.export_resume(
            user_id=owner_id,
            version_id=version_id,
            format="docx",
        )
    )

    raw = storage.saved[0][0]

    # DOCX is a ZIP archive
    assert raw[:2] == b"PK", "DOCX must be a ZIP archive"

    # Verify content by extracting text from the DOCX XML
    from docx import Document  # type: ignore[import-untyped]

    doc = Document(BytesIO(raw))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Tailored Resume" in full_text
    assert "data pipelines" in full_text
    assert "Python" in full_text
    assert "SQL" in full_text


def test_export_resume_markdown_preserves_content(tmp_path: Path) -> None:
    """MD export produces raw markdown with expected content."""
    (
        service,
        resume_versions,
        _cover_letters,
        resumes,
        storage,
    ) = _build_service(tmp_path)
    owner_id = uuid4()
    resume_id = uuid4()
    version_id = uuid4()

    resume_versions.get_by_id.return_value = SimpleNamespace(
        id=version_id,
        resume_id=resume_id,
        professional_summary="Summary text.",
        experience_json=[{"text": "Role at Acme"}],
        skills_json=[{"name": "Go"}],
        ats_score=80,
        recommendations_json=[{"text": "Improve formatting"}],
    )
    resumes.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)

    asyncio.run(
        service.export_resume(
            user_id=owner_id,
            version_id=version_id,
            format="md",
        )
    )

    raw = storage.saved[0][0].decode("utf-8")
    assert raw.startswith("# Tailored Resume")
    assert "Summary text." in raw
    assert "Role at Acme" in raw
    assert "Go" in raw
    assert "Improve formatting" in raw


def test_export_cover_letter_ownership_enforced(tmp_path: Path) -> None:
    (
        service,
        _resume_versions,
        cover_letters,
        resumes,
        _storage,
    ) = _build_service(tmp_path)
    owner_id = uuid4()
    other_user_id = uuid4()
    resume_id = uuid4()
    cover_letter_id = uuid4()

    cover_letters.get_by_id.return_value = SimpleNamespace(
        id=cover_letter_id,
        title="Title",
        greeting="Hello",
        introduction="Intro",
        body="Body",
        closing="Closing",
        tailoring_session=SimpleNamespace(resume_id=resume_id),
    )
    resumes.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)

    with pytest.raises(ResourceNotFoundException, match="Export not found"):
        asyncio.run(
            service.export_cover_letter(
                user_id=other_user_id,
                cover_letter_id=cover_letter_id,
                format="md",
            )
        )
