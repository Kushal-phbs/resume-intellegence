"""DTO exports for application services."""

from app.dto.analysis import AnalysisResult, AnalysisSkillResult
from app.dto.analytics import (
    ActivityDTO,
    AnalyticsDTO,
    DashboardDTO,
    DashboardSummaryDTO,
)
from app.dto.job_analysis import JobAnalysisResult
from app.dto.tailoring import (
    CoverLetterDTO,
    ResumeTailoringDTO,
    ResumeVersionDTO,
    TailoringSessionDTO,
)

__all__ = [
    "AnalysisResult",
    "AnalysisSkillResult",
    "DashboardDTO",
    "AnalyticsDTO",
    "ActivityDTO",
    "DashboardSummaryDTO",
    "JobAnalysisResult",
    "ResumeTailoringDTO",
    "CoverLetterDTO",
    "ResumeVersionDTO",
    "TailoringSessionDTO",
]
