from __future__ import annotations

from app.enums import ResumeFileType, ResumeStatus


def test_resume_status_values() -> None:
    assert ResumeStatus.ACTIVE == "active"
    assert ResumeStatus.ARCHIVED == "archived"
    assert ResumeStatus.DELETED == "deleted"


def test_resume_file_type_values() -> None:
    assert ResumeFileType.PDF == "pdf"
    assert ResumeFileType.DOC == "doc"
    assert ResumeFileType.DOCX == "docx"
    assert ResumeFileType.TXT == "txt"


def test_resume_enums_are_string_instances() -> None:
    assert isinstance(ResumeStatus.ACTIVE, str)
    assert isinstance(ResumeFileType.PDF, str)
