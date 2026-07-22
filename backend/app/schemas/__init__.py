"""Authentication and API schema models."""

from app.schemas.analysis import (
    KeywordResponse,
    ResumeAnalysisResponse,
    ResumeAnalysisSummary,
    ResumeAnalysisSummaryResponse,
    SkillResponse,
)
from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenPayload,
    TokenResponse,
)
from app.schemas.dashboard import (
    ActivityResponse,
    AnalyticsResponse,
    DashboardResponse,
    DashboardSummaryResponse,
    DashboardTrendsResponse,
    StatisticsResponse,
    TrendPointResponse,
)
from app.schemas.job_analysis import (
    JobAnalysisResponse,
    JobAnalysisSummaryResponse,
    KeywordMatchResponse,
    MatchedSkillResponse,
    MissingSkillResponse,
)
from app.schemas.resume import (
    ResumeListResponse,
    ResumeResponse,
    ResumeUploadMetadata,
    ResumeUploadResponse,
    ResumeVersionResponse,
)
from app.schemas.resume_tailoring import (
    CoverLetterResponse,
    ExportResponse,
    TailoringSessionResponse,
    TailoringSummaryResponse,
)
from app.schemas.resume_tailoring import (
    ResumeVersionResponse as TailoredResumeVersionResponse,
)

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "TokenResponse",
    "TokenPayload",
    "CurrentUserResponse",
    "ActivityResponse",
    "AnalyticsResponse",
    "DashboardResponse",
    "DashboardSummaryResponse",
    "StatisticsResponse",
    "DashboardTrendsResponse",
    "TrendPointResponse",
    "SkillResponse",
    "KeywordResponse",
    "ResumeAnalysisSummary",
    "ResumeAnalysisSummaryResponse",
    "ResumeAnalysisResponse",
    "MatchedSkillResponse",
    "MissingSkillResponse",
    "KeywordMatchResponse",
    "JobAnalysisSummaryResponse",
    "JobAnalysisResponse",
    "ResumeResponse",
    "ResumeListResponse",
    "ResumeVersionResponse",
    "ResumeUploadResponse",
    "ResumeUploadMetadata",
    "TailoringSessionResponse",
    "TailoringSummaryResponse",
    "TailoredResumeVersionResponse",
    "CoverLetterResponse",
    "ExportResponse",
]
