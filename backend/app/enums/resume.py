"""Resume domain enums."""

from enum import StrEnum


class ResumeStatus(StrEnum):
    """Lifecycle status of a resume record."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ResumeFileType(StrEnum):
    """Supported resume file types (matches allowed file extensions)."""

    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
