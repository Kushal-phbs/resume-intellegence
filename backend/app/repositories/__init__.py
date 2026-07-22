"""Repository abstractions and implementations."""

from app.repositories.activity_repository import ActivityRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.cover_letter_repository import CoverLetterRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.resume_version_repository import ResumeVersionRepository
from app.repositories.tailoring_session_repository import TailoringSessionRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "UserRepository",
    "ResumeRepository",
    "ResumeAnalysisRepository",
    "DashboardRepository",
    "AnalyticsRepository",
    "ActivityRepository",
    "JobDescriptionRepository",
    "JobAnalysisRepository",
    "TailoringSessionRepository",
    "ResumeVersionRepository",
    "CoverLetterRepository",
]
