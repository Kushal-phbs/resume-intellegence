"""Dashboard and analytics API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.config import settings
from app.dependencies.auth import get_current_user
from app.dependencies.dashboard import get_dashboard_service
from app.dependencies.rate_limit import limit
from app.models.user import User
from app.schemas.dashboard import (
    ActivityResponse,
    AnalyticsResponse,
    DashboardOverviewResponse,
    DashboardResponse,
    DashboardSummaryResponse,
    DashboardTrendsResponse,
    StatisticsResponse,
    TrendPointResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

_DASHBOARD_ERROR_RESPONSES = {
    401: {"description": "Authentication required"},
    404: {"description": "Dashboard data not found"},
}


def _success_rate(successful_requests: int, total_requests: int) -> float:
    if total_requests == 0:
        return 0.0
    return round((successful_requests / total_requests) * 100, 2)


@router.get(
    "",
    response_model=DashboardOverviewResponse,
    summary="Get Complete Dashboard",
    description=(
        "Return complete dashboard information for the authenticated user "
        "in a single API response."
    ),
    responses=_DASHBOARD_ERROR_RESPONSES,
)
async def get_dashboard_endpoint(
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardOverviewResponse:
    return await dashboard_service.get_dashboard_overview(user_id=current_user.id)


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get Dashboard Summary",
    description="Return summarized dashboard metrics for KPI views.",
    responses=_DASHBOARD_ERROR_RESPONSES,
)
async def get_dashboard_summary_endpoint(
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummaryResponse:
    snapshot = await dashboard_service.get_snapshot(user_id=current_user.id)
    return DashboardSummaryResponse(
        total_resumes=snapshot.total_resumes,
        total_resume_analyses=snapshot.total_resume_analyses,
        total_job_analyses=snapshot.total_job_analyses,
        total_tailoring_sessions=snapshot.total_tailoring_sessions,
        generated_cover_letters=snapshot.generated_cover_letters,
        average_resume_score=snapshot.average_resume_score,
        average_job_match_score=snapshot.average_job_match_score,
        average_tailoring_score=snapshot.average_tailoring_score,
    )


@router.get(
    "/activity",
    response_model=list[ActivityResponse],
    summary="Get Recent Activity",
    description="Return recent dashboard activity for the authenticated user.",
    responses=_DASHBOARD_ERROR_RESPONSES,
)
async def get_dashboard_activity_endpoint(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of activity events to return.",
    ),
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> list[ActivityResponse]:
    activity = await dashboard_service.get_recent_activity(
        user_id=current_user.id,
        limit=limit,
    )
    return [ActivityResponse.model_validate(item) for item in activity]


@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Get Aggregated Statistics",
    description=(
        "Return aggregated statistics for the authenticated user, including "
        "totals, averages, and AI performance metrics."
    ),
    responses=_DASHBOARD_ERROR_RESPONSES,
)
async def get_dashboard_statistics_endpoint(
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> StatisticsResponse:
    stats = await dashboard_service.get_statistics(user_id=current_user.id)
    return StatisticsResponse.model_validate(stats)


@router.get(
    "/trends",
    response_model=DashboardTrendsResponse,
    summary="Get Dashboard Trends",
    description="Return chart-friendly time-series trend data for dashboard views.",
    responses=_DASHBOARD_ERROR_RESPONSES,
)
async def get_dashboard_trends_endpoint(
    points: int = Query(
        default=12,
        ge=1,
        le=52,
        description="Number of latest historical snapshot points to return.",
    ),
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardTrendsResponse:
    trend_points = await dashboard_service.get_trends(
        user_id=current_user.id,
        points=points,
    )
    return DashboardTrendsResponse(
        points=[TrendPointResponse.model_validate(point) for point in trend_points]
    )


@router.get(
    "/performance",
    response_model=AnalyticsResponse,
    summary="Get AI Performance Metrics",
    description="Return AI processing performance metrics for the user dashboard.",
    responses=_DASHBOARD_ERROR_RESPONSES,
)
async def get_dashboard_performance_endpoint(
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> AnalyticsResponse:
    performance = await dashboard_service.get_performance(user_id=current_user.id)
    return AnalyticsResponse.model_validate(performance)


@router.post(
    "/refresh",
    response_model=DashboardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Refresh Dashboard Snapshot",
    description="Regenerate dashboard snapshot and return updated complete dashboard.",
    responses=_DASHBOARD_ERROR_RESPONSES,
)
async def refresh_dashboard_endpoint(
    _: None = Depends(
        limit(
            bucket="dashboard_refresh",
            requests=settings.rate_limit_dashboard_refresh_requests,
        )
    ),
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardResponse:
    await dashboard_service.generate_dashboard_snapshot(user_id=current_user.id)
    summary = await dashboard_service.get_dashboard_summary(user_id=current_user.id)
    success_rate = _success_rate(
        summary.analytics.successful_requests,
        summary.analytics.total_ai_requests,
    )
    return DashboardResponse(
        summary=DashboardSummaryResponse(
            total_resumes=summary.snapshot.total_resumes,
            total_resume_analyses=summary.snapshot.total_resume_analyses,
            total_job_analyses=summary.snapshot.total_job_analyses,
            total_tailoring_sessions=summary.snapshot.total_tailoring_sessions,
            generated_cover_letters=summary.snapshot.generated_cover_letters,
            average_resume_score=summary.snapshot.average_resume_score,
            average_job_match_score=summary.snapshot.average_job_match_score,
            average_tailoring_score=summary.snapshot.average_tailoring_score,
        ),
        analytics=AnalyticsResponse(
            id=summary.analytics.id,
            user_id=summary.analytics.user_id,
            total_ai_requests=summary.analytics.total_ai_requests,
            total_tokens_used=summary.analytics.total_tokens_used,
            successful_requests=summary.analytics.successful_requests,
            failed_requests=summary.analytics.failed_requests,
            success_rate=success_rate,
            average_processing_time_ms=summary.analytics.average_processing_time_ms,
            last_activity_at=summary.analytics.last_activity_at,
            created_at=summary.analytics.created_at,
            updated_at=summary.analytics.updated_at,
        ),
        recent_activity=[
            ActivityResponse.model_validate(item) for item in summary.recent_activity
        ],
    )
