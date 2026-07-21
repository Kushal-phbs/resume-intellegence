"""Shared enum definitions."""

from app.enums.analysis import AnalysisStatus, SkillCategory
from app.enums.auth import TokenType, UserRole
from app.enums.resume import ResumeFileType, ResumeStatus

__all__ = [
    "UserRole",
    "TokenType",
    "ResumeStatus",
    "ResumeFileType",
    "AnalysisStatus",
    "SkillCategory",
]
