"""Job intelligence analysis API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from app.config import settings
from app.dependencies.auth import get_current_user
from app.dependencies.job_analysis import get_job_analysis_service
from app.dependencies.rate_limit import limit
from app.models.user import User
from app.schemas.job_analysis import (
    JobAnalysisResponse,
    JobAnalysisSummaryResponse,
    KeywordMatchResponse,
    MatchedSkillResponse,
    MissingSkillResponse,
)
from app.services.job_analysis_service import JobAnalysisService

router = APIRouter(prefix="/job-analysis", tags=["Job Analysis"])

_JOB_ANALYSIS_ERROR_RESPONSES = {
    401: {"description": "Authentication required"},
    404: {"description": "Resume, job description, or analysis not found"},
    502: {"description": "Analysis failed"},
}


@router.get(
    "/history",
    response_model=list[JobAnalysisSummaryResponse],
    summary="List Job Analysis History",
    description="List previous job analyses owned by the authenticated user.",
    responses=_JOB_ANALYSIS_ERROR_RESPONSES,
)
async def get_job_analysis_history_endpoint(
    current_user: User = Depends(get_current_user),
    job_analysis_service: JobAnalysisService = Depends(get_job_analysis_service),
) -> list[JobAnalysisSummaryResponse]:
    """Return previous job analyses for the authenticated user."""
    return await job_analysis_service.list_history(user_id=current_user.id)


@router.post(
    "/{resume_id}/{job_id}",
    response_model=JobAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze Resume Against Job",
    description=(
        "Run a job-match analysis using a resume and job description owned by "
        "the authenticated user."
    ),
    responses=_JOB_ANALYSIS_ERROR_RESPONSES,
)
async def analyze_job_endpoint(
    resume_id: UUID = Path(description="Resume identifier."),
    job_id: UUID = Path(description="Job description identifier."),
    _: None = Depends(
        limit(
            bucket="job_analysis",
            requests=settings.rate_limit_job_analysis_requests,
        )
    ),
    current_user: User = Depends(get_current_user),
    job_analysis_service: JobAnalysisService = Depends(get_job_analysis_service),
) -> JobAnalysisResponse:
    """Run job analysis for one resume and one job description."""
    return await job_analysis_service.analyze_job_match(
        user_id=current_user.id,
        resume_id=resume_id,
        job_description_id=job_id,
    )


@router.get(
    "/{analysis_id}",
    response_model=JobAnalysisResponse,
    summary="Get Job Analysis",
    description="Return complete details for a stored job analysis.",
    responses=_JOB_ANALYSIS_ERROR_RESPONSES,
)
async def get_job_analysis_endpoint(
    analysis_id: UUID = Path(description="Job analysis identifier."),
    current_user: User = Depends(get_current_user),
    job_analysis_service: JobAnalysisService = Depends(get_job_analysis_service),
) -> JobAnalysisResponse:
    """Return full job analysis details."""
    return await job_analysis_service.get_analysis(
        user_id=current_user.id,
        analysis_id=analysis_id,
    )


@router.get(
    "/{analysis_id}/summary",
    response_model=JobAnalysisSummaryResponse,
    summary="Get Job Analysis Summary",
    description="Return summary scores and key insights for a job analysis.",
    responses=_JOB_ANALYSIS_ERROR_RESPONSES,
)
async def get_job_analysis_summary_endpoint(
    analysis_id: UUID = Path(description="Job analysis identifier."),
    current_user: User = Depends(get_current_user),
    job_analysis_service: JobAnalysisService = Depends(get_job_analysis_service),
) -> JobAnalysisSummaryResponse:
    """Return match/ATS scores and structured insight fields."""
    return await job_analysis_service.get_summary(
        user_id=current_user.id,
        analysis_id=analysis_id,
    )


@router.get(
    "/{analysis_id}/matched-skills",
    response_model=list[MatchedSkillResponse],
    summary="Get Matched Skills",
    description="Return skills that match between resume and job requirements.",
    responses=_JOB_ANALYSIS_ERROR_RESPONSES,
)
async def get_job_analysis_matched_skills_endpoint(
    analysis_id: UUID = Path(description="Job analysis identifier."),
    current_user: User = Depends(get_current_user),
    job_analysis_service: JobAnalysisService = Depends(get_job_analysis_service),
) -> list[MatchedSkillResponse]:
    """Return matched skills from one job analysis."""
    return await job_analysis_service.get_matched_skills(
        user_id=current_user.id,
        analysis_id=analysis_id,
    )


@router.get(
    "/{analysis_id}/missing-skills",
    response_model=list[MissingSkillResponse],
    summary="Get Missing Skills",
    description="Return skills required by the job but missing from the resume.",
    responses=_JOB_ANALYSIS_ERROR_RESPONSES,
)
async def get_job_analysis_missing_skills_endpoint(
    analysis_id: UUID = Path(description="Job analysis identifier."),
    current_user: User = Depends(get_current_user),
    job_analysis_service: JobAnalysisService = Depends(get_job_analysis_service),
) -> list[MissingSkillResponse]:
    """Return missing skills from one job analysis."""
    return await job_analysis_service.get_missing_skills(
        user_id=current_user.id,
        analysis_id=analysis_id,
    )


@router.get(
    "/{analysis_id}/keywords",
    response_model=list[KeywordMatchResponse],
    summary="Get Keyword Matches",
    description="Return keyword matches extracted from the job analysis.",
    responses=_JOB_ANALYSIS_ERROR_RESPONSES,
)
async def get_job_analysis_keywords_endpoint(
    analysis_id: UUID = Path(description="Job analysis identifier."),
    current_user: User = Depends(get_current_user),
    job_analysis_service: JobAnalysisService = Depends(get_job_analysis_service),
) -> list[KeywordMatchResponse]:
    """Return matched keywords from one job analysis."""
    return await job_analysis_service.get_keyword_matches(
        user_id=current_user.id,
        analysis_id=analysis_id,
    )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Job Analysis",
    description="Delete a job analysis record owned by the authenticated user.",
    responses={
        204: {"description": "Job analysis deleted."},
        401: {"description": "Authentication required"},
        404: {"description": "Job analysis not found"},
    },
)
async def delete_job_analysis_endpoint(
    analysis_id: UUID = Path(description="Job analysis identifier."),
    current_user: User = Depends(get_current_user),
    job_analysis_service: JobAnalysisService = Depends(get_job_analysis_service),
) -> None:
    """Delete one job analysis record owned by the authenticated user."""
    await job_analysis_service.delete_analysis(
        user_id=current_user.id,
        analysis_id=analysis_id,
    )
