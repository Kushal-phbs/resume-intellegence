"""Shared enum definitions."""

from app.enums.analysis import AnalysisStatus, SkillCategory
from app.enums.analytics import ActivityType, EntityType
from app.enums.auth import TokenType, UserRole
from app.enums.job_analysis import JobAnalysisStatus
from app.enums.resume import ResumeFileType, ResumeStatus
from app.enums.tailoring import TailoringStatus

__all__ = [
    "UserRole",
    "TokenType",
    "ResumeStatus",
    "ResumeFileType",
    "ActivityType",
    "EntityType",
    "AnalysisStatus",
    "JobAnalysisStatus",
    "TailoringStatus",
    "SkillCategory",
]
