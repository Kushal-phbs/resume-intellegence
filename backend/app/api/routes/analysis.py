"""Resume intelligence analysis API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.analysis import get_analysis_service
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.analysis import (
    KeywordResponse,
    ResumeAnalysisResponse,
    ResumeAnalysisSummaryResponse,
    SkillResponse,
)
from app.services.resume_analysis_service import ResumeAnalysisService

router = APIRouter(prefix="/analysis", tags=["Analysis"])

_ANALYSIS_ERROR_RESPONSES = {
    401: {"description": "Authentication required"},
    404: {"description": "Resume or analysis not found"},
    409: {"description": "Analysis already in progress"},
    502: {"description": "Analysis failed"},
}


@router.post(
    "/{resume_id}",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    responses=_ANALYSIS_ERROR_RESPONSES,
)
async def analyze_resume_endpoint(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    analysis_service: ResumeAnalysisService = Depends(get_analysis_service),
) -> ResumeAnalysisResponse:
    """Analyze the latest uploaded version of a resume owned by the user."""
    return await analysis_service.analyze_resume(current_user.id, resume_id)


@router.get(
    "/{resume_id}",
    response_model=ResumeAnalysisResponse,
    responses=_ANALYSIS_ERROR_RESPONSES,
)
async def get_latest_analysis_endpoint(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    analysis_service: ResumeAnalysisService = Depends(get_analysis_service),
) -> ResumeAnalysisResponse:
    """Return the latest completed analysis for a resume owned by the user."""
    return await analysis_service.get_latest_analysis(current_user.id, resume_id)


@router.get(
    "/{resume_id}/summary",
    response_model=ResumeAnalysisSummaryResponse,
    responses=_ANALYSIS_ERROR_RESPONSES,
)
async def get_analysis_summary_endpoint(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    analysis_service: ResumeAnalysisService = Depends(get_analysis_service),
) -> ResumeAnalysisSummaryResponse:
    """Return a lightweight summary for the latest completed analysis."""
    return await analysis_service.get_latest_summary(current_user.id, resume_id)


@router.get(
    "/{resume_id}/skills",
    response_model=list[SkillResponse],
    responses=_ANALYSIS_ERROR_RESPONSES,
)
async def get_analysis_skills_endpoint(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    analysis_service: ResumeAnalysisService = Depends(get_analysis_service),
) -> list[SkillResponse]:
    """Return the extracted skills from the latest completed analysis."""
    return await analysis_service.get_latest_skills(current_user.id, resume_id)


@router.get(
    "/{resume_id}/keywords",
    response_model=list[KeywordResponse],
    responses=_ANALYSIS_ERROR_RESPONSES,
)
async def get_analysis_keywords_endpoint(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    analysis_service: ResumeAnalysisService = Depends(get_analysis_service),
) -> list[KeywordResponse]:
    """Return the extracted keywords from the latest completed analysis."""
    return await analysis_service.get_latest_keywords(current_user.id, resume_id)


@router.get(
    "/{resume_id}/history",
    response_model=list[ResumeAnalysisSummaryResponse],
    responses=_ANALYSIS_ERROR_RESPONSES,
)
async def get_analysis_history_endpoint(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    analysis_service: ResumeAnalysisService = Depends(get_analysis_service),
) -> list[ResumeAnalysisSummaryResponse]:
    """Return all stored analyses for a resume, newest first."""
    return await analysis_service.list_analyses(current_user.id, resume_id)


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "Analysis not found"},
    },
)
async def delete_analysis_endpoint(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    analysis_service: ResumeAnalysisService = Depends(get_analysis_service),
) -> None:
    """Delete one analysis record owned by the authenticated user."""
    await analysis_service.delete_analysis(current_user.id, analysis_id)
