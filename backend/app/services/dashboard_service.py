"""Business logic for user dashboard analytics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.config import settings
from app.core.cache import RedisCache
from app.core.exceptions import AppException, ResourceNotFoundException
from app.core.logging import logger
from app.dto.analytics import (
    ActivityDTO,
    AnalyticsDTO,
    DashboardDTO,
    DashboardSummaryDTO,
)
from app.enums import AnalysisStatus, JobAnalysisStatus, UserRole
from app.enums.analytics import ActivityType, EntityType
from app.repositories.activity_repository import ActivityRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.schemas.dashboard import (
    DashboardAnalyticsSummaryResponse,
    DashboardNotificationResponse,
    DashboardOverviewResponse,
    DashboardQuickActionResponse,
    DashboardRecentResumeResponse,
    DashboardStatisticsOverview,
    DashboardSuggestionResponse,
    DashboardUserResponse,
)


@dataclass(slots=True)
class _SuggestionCandidate:
    source: str
    analysis_id: UUID
    resume_id: UUID
    suggestion: str
    created_at: datetime


class DashboardService:
    """Coordinates dashboard snapshots, analytics counters, and activity history."""

    def __init__(
        self,
        dashboard_repository: DashboardRepository,
        analytics_repository: AnalyticsRepository,
        activity_repository: ActivityRepository,
        resume_repository: ResumeRepository | None = None,
        resume_analysis_repository: ResumeAnalysisRepository | None = None,
        job_analysis_repository: JobAnalysisRepository | None = None,
        notification_repository: NotificationRepository | None = None,
        user_repository: UserRepository | None = None,
        cache_service: Any | None = None,
    ) -> None:
        self._dashboards = dashboard_repository
        self._analytics = analytics_repository
        self._activities = activity_repository
        self._resumes = resume_repository
        self._resume_analyses = resume_analysis_repository
        self._job_analyses = job_analysis_repository
        self._notifications = notification_repository
        self._users = user_repository
        self._cache = cache_service or RedisCache(
            redis_url=settings.redis_url,
            default_ttl_seconds=settings.cache_default_ttl_seconds,
            enabled=settings.redis_enabled,
        )

    async def get_dashboard_overview(
        self,
        *,
        user_id: UUID,
    ) -> DashboardOverviewResponse:
        """Return a unified dashboard payload for one-call frontend rendering."""
        user = await self._get_user(user_id)
        resumes = await self._get_resumes(user_id)
        resume_analyses = await self._get_resume_analyses(user_id)
        job_analyses = await self._get_job_analyses(user_id)
        analytics = await self._analytics.get_by_user(user_id)
        notifications = await self._get_unread_notifications(user_id)

        completed_resume_analyses = [
            item
            for item in resume_analyses
            if item.analysis_status == AnalysisStatus.COMPLETED.value
        ]
        completed_job_analyses = [
            item
            for item in job_analyses
            if item.analysis_status == JobAnalysisStatus.COMPLETED.value
        ]

        completed_resume_analyses.sort(
            key=lambda item: item.created_at or datetime.min.replace(tzinfo=UTC)
        )
        ats_scores = [
            int(item.ats_score)
            for item in completed_resume_analyses
            if item.ats_score is not None
        ]

        statistics = DashboardStatisticsOverview(
            total_resumes=len(resumes),
            average_ats_score=(
                round(sum(ats_scores) / len(ats_scores), 2) if ats_scores else None
            ),
            highest_ats_score=max(ats_scores) if ats_scores else None,
            improvement_percentage=self._calculate_improvement_percentage(ats_scores),
            improvement_streak=self._calculate_improvement_streak(ats_scores),
        )

        latest_scores_by_resume: dict[UUID, int] = {}
        for analysis in sorted(
            completed_resume_analyses,
            key=lambda item: item.created_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        ):
            if analysis.ats_score is None:
                continue
            if analysis.resume_id not in latest_scores_by_resume:
                latest_scores_by_resume[analysis.resume_id] = int(analysis.ats_score)

        recent_resumes = [
            DashboardRecentResumeResponse(
                id=resume.id,
                title=resume.title,
                is_primary=resume.is_primary,
                latest_ats_score=latest_scores_by_resume.get(resume.id),
                created_at=resume.created_at,
                updated_at=resume.updated_at,
            )
            for resume in sorted(
                resumes,
                key=lambda item: (
                    item.updated_at,
                    item.created_at,
                    item.id,
                ),
                reverse=True,
            )[:5]
        ]

        score_distribution = self._build_score_distribution(ats_scores)

        total_ai_requests = analytics.total_ai_requests if analytics is not None else 0
        successful_requests = (
            analytics.successful_requests if analytics is not None else 0
        )
        failed_requests = analytics.failed_requests if analytics is not None else 0
        success_rate = (
            round((successful_requests / total_ai_requests) * 100, 2)
            if total_ai_requests
            else 0.0
        )
        analytics_summary = DashboardAnalyticsSummaryResponse(
            total_ai_requests=total_ai_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            total_tokens_used=(
                analytics.total_tokens_used if analytics is not None else 0
            ),
            average_processing_time_ms=(
                round(float(analytics.average_processing_time_ms), 2)
                if analytics is not None
                and analytics.average_processing_time_ms is not None
                else None
            ),
            last_activity_at=(
                analytics.last_activity_at if analytics is not None else None
            ),
        )

        latest_ai_suggestions = self._collect_latest_ai_suggestions(
            completed_resume_analyses,
            completed_job_analyses,
        )

        unread_notifications = [
            DashboardNotificationResponse(
                id=notification.id,
                activity_type=ActivityType(
                    self._map_notification_type_to_activity_type(notification.type)
                ),
                entity_type=EntityType(
                    self._map_notification_type_to_entity_type(notification.type)
                ),
                entity_id=(
                    notification.metadata_json.get("entity_id")
                    if isinstance(notification.metadata_json, dict)
                    else None
                ),
                message=notification.message,
                created_at=notification.created_at,
                metadata_json=notification.metadata_json,
            )
            for notification in notifications
        ]

        quick_actions = self._build_quick_actions(
            total_resumes=len(resumes),
            has_resume_analysis=bool(completed_resume_analyses),
            has_job_analysis=bool(completed_job_analyses),
            average_ats_score=statistics.average_ats_score,
            has_unread_notifications=bool(unread_notifications),
            has_missing_skills=any(
                bool(getattr(analysis, "missing_skills", []))
                for analysis in completed_job_analyses
            ),
        )

        return DashboardOverviewResponse(
            user=DashboardUserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=UserRole(user.role),
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
            ),
            statistics=statistics,
            recent_resumes=recent_resumes,
            score_distribution=score_distribution,
            analytics_summary=analytics_summary,
            latest_ai_suggestions=latest_ai_suggestions,
            unread_notifications=unread_notifications,
            quick_actions=quick_actions,
        )

    async def calculate_dashboard_metrics(self, *, user_id: UUID) -> DashboardDTO:
        metrics = await self._dashboards.calculate_metrics(user_id)
        return DashboardDTO(
            user_id=user_id,
            total_resumes=int(metrics["total_resumes"] or 0),
            total_resume_analyses=int(metrics["total_resume_analyses"] or 0),
            total_job_analyses=int(metrics["total_job_analyses"] or 0),
            total_tailoring_sessions=int(metrics["total_tailoring_sessions"] or 0),
            average_resume_score=self._round_average(metrics["average_resume_score"]),
            average_job_match_score=self._round_average(
                metrics["average_job_match_score"]
            ),
            average_tailoring_score=self._round_average(
                metrics["average_tailoring_score"]
            ),
            generated_cover_letters=int(metrics["generated_cover_letters"] or 0),
        )

    async def generate_dashboard_snapshot(self, *, user_id: UUID) -> DashboardDTO:
        metrics = await self.calculate_dashboard_metrics(user_id=user_id)
        snapshot = await self._dashboards.create(
            user_id=user_id,
            total_resumes=metrics.total_resumes,
            total_resume_analyses=metrics.total_resume_analyses,
            total_job_analyses=metrics.total_job_analyses,
            total_tailoring_sessions=metrics.total_tailoring_sessions,
            average_resume_score=metrics.average_resume_score,
            average_job_match_score=metrics.average_job_match_score,
            average_tailoring_score=metrics.average_tailoring_score,
            generated_cover_letters=metrics.generated_cover_letters,
        )
        await self._invalidate_dashboard_cache(user_id)
        return self._to_dashboard_dto(snapshot)

    async def update_analytics(
        self,
        *,
        user_id: UUID,
        tokens_used: int,
        processing_time_ms: float,
        successful: bool,
        activity_at: datetime | None = None,
    ) -> AnalyticsDTO:
        current = await self._analytics.get_by_user(user_id)
        now = activity_at or datetime.now(UTC)

        if current is None:
            created = await self._analytics.create(
                user_id=user_id,
                total_ai_requests=1,
                total_tokens_used=max(tokens_used, 0),
                successful_requests=1 if successful else 0,
                failed_requests=0 if successful else 1,
                average_processing_time_ms=max(processing_time_ms, 0.0),
                last_activity_at=now,
            )
            await self._invalidate_dashboard_cache(user_id)
            return self._to_analytics_dto(created)

        new_total_requests = current.total_ai_requests + 1
        safe_time = max(processing_time_ms, 0.0)
        previous_average = current.average_processing_time_ms or 0.0
        new_average_time = (
            (previous_average * current.total_ai_requests) + safe_time
        ) / new_total_requests

        updated = await self._analytics.update(
            current.id,
            total_ai_requests=new_total_requests,
            total_tokens_used=current.total_tokens_used + max(tokens_used, 0),
            successful_requests=current.successful_requests + (1 if successful else 0),
            failed_requests=current.failed_requests + (0 if successful else 1),
            average_processing_time_ms=new_average_time,
            last_activity_at=now,
        )
        await self._invalidate_dashboard_cache(user_id)
        if updated is None:
            return self._to_analytics_dto(current)
        return self._to_analytics_dto(updated)

    async def record_activity(
        self,
        *,
        user_id: UUID,
        activity_type: ActivityType,
        entity_type: EntityType,
        entity_id: UUID | None,
        metadata_json: dict[str, object] | None = None,
    ) -> ActivityDTO:
        activity = await self._activities.record_activity(
            user_id=user_id,
            activity_type=activity_type,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata_json,
        )
        await self._invalidate_dashboard_cache(user_id)
        return self._to_activity_dto(activity)

    async def get_dashboard_summary(
        self,
        *,
        user_id: UUID,
        activity_limit: int = 20,
    ) -> DashboardSummaryDTO:
        if self._cache is not None:
            cached = await self._cache_get(
                namespace=self._summary_namespace(user_id),
                key=f"limit:{activity_limit}",
            )
            if cached is not None:
                return DashboardSummaryDTO.model_validate(cached)

        latest_snapshot = await self._dashboards.latest_snapshot(user_id)
        if latest_snapshot is None:
            snapshot = await self.generate_dashboard_snapshot(user_id=user_id)
        else:
            snapshot = self._to_dashboard_dto(latest_snapshot)

        analytics = await self._analytics.get_by_user(user_id)
        if analytics is None:
            analytics_dto = AnalyticsDTO(
                user_id=user_id,
                total_ai_requests=0,
                total_tokens_used=0,
                successful_requests=0,
                failed_requests=0,
                average_processing_time_ms=None,
                last_activity_at=None,
            )
        else:
            analytics_dto = self._to_analytics_dto(analytics)

        activities = await self._activities.list_recent_activity(
            user_id,
            limit=activity_limit,
        )
        summary = DashboardSummaryDTO(
            snapshot=snapshot,
            analytics=analytics_dto,
            recent_activity=[self._to_activity_dto(item) for item in activities],
        )
        if self._cache is not None:
            await self._cache_set(
                namespace=self._summary_namespace(user_id),
                key=f"limit:{activity_limit}",
                value=summary.model_dump(mode="json"),
                ttl_seconds=self._ttl_seconds(
                    settings.cache_dashboard_summary_ttl_seconds
                ),
            )
        return summary

    async def get_snapshot(self, *, user_id: UUID) -> DashboardDTO:
        latest_snapshot = await self._dashboards.latest_snapshot(user_id)
        if latest_snapshot is None:
            return await self.generate_dashboard_snapshot(user_id=user_id)
        return self._to_dashboard_dto(latest_snapshot)

    async def get_recent_activity(
        self,
        *,
        user_id: UUID,
        limit: int = 20,
    ) -> list[ActivityDTO]:
        activity_rows = await self._activities.list_recent_activity(
            user_id,
            limit=limit,
        )
        return [self._to_activity_dto(item) for item in activity_rows]

    async def get_statistics(self, *, user_id: UUID) -> dict[str, float | int | None]:
        if self._cache is not None:
            cached = await self._cache_get(
                namespace=self._statistics_namespace(user_id),
                key="current",
            )
            if cached is not None:
                return dict(cached)

        summary = await self.get_dashboard_summary(user_id=user_id, activity_limit=1)
        total_analyses = (
            summary.snapshot.total_resume_analyses + summary.snapshot.total_job_analyses
        )
        total_requests = summary.analytics.total_ai_requests
        success_rate = (
            round((summary.analytics.successful_requests / total_requests) * 100, 2)
            if total_requests
            else 0.0
        )

        result = {
            "total_resumes": summary.snapshot.total_resumes,
            "total_analyses": total_analyses,
            "total_tailoring_sessions": summary.snapshot.total_tailoring_sessions,
            "total_exports": summary.snapshot.generated_cover_letters,
            "average_ats_score": summary.snapshot.average_resume_score,
            "average_job_match_score": summary.snapshot.average_job_match_score,
            "average_tailoring_score": summary.snapshot.average_tailoring_score,
            "total_ai_requests": total_requests,
            "success_rate": success_rate,
            "average_processing_time_ms": summary.analytics.average_processing_time_ms,
            "total_tokens_used": summary.analytics.total_tokens_used,
        }
        if self._cache is not None:
            await self._cache_set(
                namespace=self._statistics_namespace(user_id),
                key="current",
                value=result,
                ttl_seconds=self._ttl_seconds(
                    settings.cache_dashboard_statistics_ttl_seconds
                ),
            )
        return result

    async def get_trends(
        self,
        *,
        user_id: UUID,
        points: int = 12,
    ) -> list[dict[str, float | int | datetime | None]]:
        if self._cache is not None:
            cached = await self._cache_get(
                namespace=self._trends_namespace(user_id),
                key=f"points:{points}",
            )
            if cached is not None:
                return list(cached)

        snapshots = await self._dashboards.get_by_user(user_id)
        selected = list(reversed(snapshots[:points]))
        trend_points: list[dict[str, float | int | datetime | None]] = []
        for snapshot in selected:
            trend_points.append(
                {
                    "timestamp": snapshot.created_at,
                    "total_resumes": snapshot.total_resumes,
                    "total_resume_analyses": snapshot.total_resume_analyses,
                    "total_job_analyses": snapshot.total_job_analyses,
                    "total_tailoring_sessions": snapshot.total_tailoring_sessions,
                    "generated_cover_letters": snapshot.generated_cover_letters,
                    "average_resume_score": self._round_average(
                        snapshot.average_resume_score
                    ),
                    "average_job_match_score": self._round_average(
                        snapshot.average_job_match_score
                    ),
                    "average_tailoring_score": self._round_average(
                        snapshot.average_tailoring_score
                    ),
                }
            )
        if self._cache is not None:
            await self._cache_set(
                namespace=self._trends_namespace(user_id),
                key=f"points:{points}",
                value=trend_points,
                ttl_seconds=self._ttl_seconds(
                    settings.cache_dashboard_trends_ttl_seconds
                ),
            )
        return trend_points

    async def get_performance(
        self,
        *,
        user_id: UUID,
    ) -> dict[str, float | int | UUID | datetime | None]:
        if self._cache is not None:
            cached = await self._cache_get(
                namespace=self._performance_namespace(user_id),
                key="current",
            )
            if cached is not None:
                return dict(cached)

        analytics = await self._analytics.get_by_user(user_id)
        if analytics is None:
            empty_result = {
                "id": None,
                "user_id": user_id,
                "total_ai_requests": 0,
                "total_tokens_used": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "success_rate": 0.0,
                "average_processing_time_ms": None,
                "last_activity_at": None,
                "created_at": None,
                "updated_at": None,
            }
            if self._cache is not None:
                await self._cache_set(
                    namespace=self._performance_namespace(user_id),
                    key="current",
                    value=empty_result,
                    ttl_seconds=self._ttl_seconds(
                        settings.cache_dashboard_performance_ttl_seconds
                    ),
                )
            return empty_result

        total_requests = analytics.total_ai_requests
        success_rate = (
            round((analytics.successful_requests / total_requests) * 100, 2)
            if total_requests
            else 0.0
        )
        result = {
            "id": analytics.id,
            "user_id": analytics.user_id,
            "total_ai_requests": analytics.total_ai_requests,
            "total_tokens_used": analytics.total_tokens_used,
            "successful_requests": analytics.successful_requests,
            "failed_requests": analytics.failed_requests,
            "success_rate": success_rate,
            "average_processing_time_ms": (
                round(float(analytics.average_processing_time_ms), 2)
                if analytics.average_processing_time_ms is not None
                else None
            ),
            "last_activity_at": analytics.last_activity_at,
            "created_at": analytics.created_at,
            "updated_at": analytics.updated_at,
        }
        if self._cache is not None:
            await self._cache_set(
                namespace=self._performance_namespace(user_id),
                key="current",
                value=result,
                ttl_seconds=self._ttl_seconds(
                    settings.cache_dashboard_performance_ttl_seconds
                ),
            )
        return result

    async def _invalidate_dashboard_cache(self, user_id: UUID) -> None:
        if self._cache is None:
            return
        await self._cache_delete_pattern(self._summary_pattern(user_id))
        await self._cache_delete_pattern(self._statistics_pattern(user_id))
        await self._cache_delete_pattern(self._trends_pattern(user_id))
        await self._cache_delete_pattern(self._performance_pattern(user_id))

    def _summary_namespace(self, user_id: UUID) -> str:
        return f"dashboard_summary:{user_id}"

    def _summary_pattern(self, user_id: UUID) -> str:
        return f"{self._summary_namespace(user_id)}:*"

    def _statistics_namespace(self, user_id: UUID) -> str:
        return f"dashboard_statistics:{user_id}"

    def _statistics_pattern(self, user_id: UUID) -> str:
        return f"{self._statistics_namespace(user_id)}:*"

    def _trends_namespace(self, user_id: UUID) -> str:
        return f"dashboard_trends:{user_id}"

    def _trends_pattern(self, user_id: UUID) -> str:
        return f"{self._trends_namespace(user_id)}:*"

    def _performance_namespace(self, user_id: UUID) -> str:
        return f"dashboard_performance:{user_id}"

    def _performance_pattern(self, user_id: UUID) -> str:
        return f"{self._performance_namespace(user_id)}:*"

    def _cache_key(self, namespace: str, key: str) -> str:
        return f"{namespace}:{key}"

    def _ttl_seconds(self, configured_ttl_seconds: int) -> int:
        return max(300, min(int(configured_ttl_seconds), 600))

    async def _cache_get(self, *, namespace: str, key: str) -> Any | None:
        if self._cache is None:
            return None

        cache_key = self._cache_key(namespace, key)
        try:
            cached = await self._cache.get(cache_key)
        except TypeError:
            cached = await self._cache.get(namespace=namespace, key=key)

        if cached is None:
            logger.debug("cache.miss key=%s", cache_key)
            return None

        logger.debug("cache.hit key=%s", cache_key)
        return cached

    async def _cache_set(
        self,
        *,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: int,
    ) -> None:
        if self._cache is None:
            return

        cache_key = self._cache_key(namespace, key)
        try:
            await self._cache.set(cache_key, value, ttl_seconds)
        except TypeError:
            await self._cache.set(
                namespace=namespace,
                key=key,
                value=value,
                ttl_seconds=ttl_seconds,
            )

    async def _cache_delete_pattern(self, pattern: str) -> None:
        if self._cache is None:
            return

        delete_pattern = getattr(self._cache, "delete_pattern", None)
        if callable(delete_pattern):
            await delete_pattern(pattern)
            return

        invalidate = getattr(self._cache, "invalidate", None)
        if callable(invalidate):
            await invalidate(pattern[:-1] if pattern.endswith("*") else pattern)

    def _round_average(self, value: float | int | None) -> float | None:
        if value is None:
            return None
        return round(float(value), 2)

    def _to_dashboard_dto(self, snapshot) -> DashboardDTO:
        return DashboardDTO(
            id=snapshot.id,
            user_id=snapshot.user_id,
            total_resumes=snapshot.total_resumes,
            total_resume_analyses=snapshot.total_resume_analyses,
            total_job_analyses=snapshot.total_job_analyses,
            total_tailoring_sessions=snapshot.total_tailoring_sessions,
            average_resume_score=self._round_average(snapshot.average_resume_score),
            average_job_match_score=self._round_average(
                snapshot.average_job_match_score
            ),
            average_tailoring_score=self._round_average(
                snapshot.average_tailoring_score
            ),
            generated_cover_letters=snapshot.generated_cover_letters,
            created_at=snapshot.created_at,
            updated_at=snapshot.updated_at,
        )

    def _to_analytics_dto(self, analytics) -> AnalyticsDTO:
        return AnalyticsDTO(
            id=analytics.id,
            user_id=analytics.user_id,
            total_ai_requests=analytics.total_ai_requests,
            total_tokens_used=analytics.total_tokens_used,
            successful_requests=analytics.successful_requests,
            failed_requests=analytics.failed_requests,
            average_processing_time_ms=(
                round(float(analytics.average_processing_time_ms), 2)
                if analytics.average_processing_time_ms is not None
                else None
            ),
            last_activity_at=analytics.last_activity_at,
            created_at=analytics.created_at,
            updated_at=analytics.updated_at,
        )

    def _to_activity_dto(self, activity) -> ActivityDTO:
        return ActivityDTO(
            id=activity.id,
            user_id=activity.user_id,
            activity_type=ActivityType(activity.activity_type),
            entity_type=EntityType(activity.entity_type),
            entity_id=activity.entity_id,
            metadata_json=activity.metadata_json,
            created_at=activity.created_at,
        )

    async def _get_user(self, user_id: UUID):
        if self._users is None:
            raise AppException("Dashboard service misconfigured", status_code=500)
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundException("Dashboard data not found")
        return user

    async def _get_resumes(self, user_id: UUID):
        if self._resumes is None:
            raise AppException("Dashboard service misconfigured", status_code=500)
        return await self._resumes.list_by_user(user_id)

    async def _get_resume_analyses(self, user_id: UUID):
        if self._resume_analyses is None:
            raise AppException("Dashboard service misconfigured", status_code=500)
        return await self._resume_analyses.list_by_user(user_id)

    async def _get_job_analyses(self, user_id: UUID):
        if self._job_analyses is None:
            raise AppException("Dashboard service misconfigured", status_code=500)
        return await self._job_analyses.list_by_user(user_id)

    async def _get_unread_notifications(self, user_id: UUID):
        if self._notifications is None:
            raise AppException("Dashboard service misconfigured", status_code=500)
        return await self._notifications.list_unread(user_id, limit=100)

    def _build_score_distribution(self, ats_scores: list[int]) -> dict[str, int]:
        distribution = {
            "0-20": 0,
            "21-40": 0,
            "41-60": 0,
            "61-80": 0,
            "81-100": 0,
        }
        for score in ats_scores:
            if score <= 20:
                distribution["0-20"] += 1
            elif score <= 40:
                distribution["21-40"] += 1
            elif score <= 60:
                distribution["41-60"] += 1
            elif score <= 80:
                distribution["61-80"] += 1
            else:
                distribution["81-100"] += 1
        return distribution

    def _calculate_improvement_percentage(self, ats_scores: list[int]) -> float:
        if len(ats_scores) < 2:
            return 0.0

        baseline = ats_scores[0]
        latest = ats_scores[-1]

        if baseline <= 0:
            return 100.0 if latest > 0 else 0.0

        return round(((latest - baseline) / baseline) * 100, 2)

    def _calculate_improvement_streak(self, ats_scores: list[int]) -> int:
        if len(ats_scores) < 2:
            return 0

        streak = 0
        for index in range(len(ats_scores) - 1, 0, -1):
            if ats_scores[index] > ats_scores[index - 1]:
                streak += 1
                continue
            break
        return streak

    def _collect_latest_ai_suggestions(
        self,
        completed_resume_analyses,
        completed_job_analyses,
    ) -> list[DashboardSuggestionResponse]:
        candidates: list[_SuggestionCandidate] = []

        for analysis in completed_resume_analyses:
            for recommendation in (analysis.recommendations or [])[:2]:
                if not recommendation:
                    continue
                created_at = analysis.created_at or datetime.now(UTC)
                candidates.append(
                    _SuggestionCandidate(
                        source="resume_analysis",
                        analysis_id=analysis.id,
                        resume_id=analysis.resume_id,
                        suggestion=recommendation,
                        created_at=created_at,
                    )
                )

        for analysis in completed_job_analyses:
            for recommendation in (analysis.recommendations or [])[:2]:
                if not recommendation:
                    continue
                created_at = analysis.created_at or datetime.now(UTC)
                candidates.append(
                    _SuggestionCandidate(
                        source="job_analysis",
                        analysis_id=analysis.id,
                        resume_id=analysis.resume_id,
                        suggestion=recommendation,
                        created_at=created_at,
                    )
                )

        candidates.sort(key=lambda item: item.created_at, reverse=True)
        return [
            DashboardSuggestionResponse(
                source=item.source,
                analysis_id=item.analysis_id,
                resume_id=item.resume_id,
                suggestion=item.suggestion,
                created_at=item.created_at,
            )
            for item in candidates[:10]
        ]

    def _activity_message(self, activity_type: str, metadata: dict[str, object]) -> str:
        metadata_message = metadata.get("message")
        if isinstance(metadata_message, str) and metadata_message.strip():
            return metadata_message
        normalized = activity_type.replace("_", " ").strip()
        if not normalized:
            return "New dashboard activity"
        return normalized.capitalize()

    def _map_notification_type_to_activity_type(self, notification_type: str) -> str:
        mapping = {
            "resume_uploaded": ActivityType.RESUME_UPLOADED.value,
            "resume_analysis_completed": ActivityType.RESUME_ANALYZED.value,
            "job_analysis_completed": ActivityType.JOB_ANALYZED.value,
            "resume_tailoring_completed": ActivityType.RESUME_TAILORED.value,
            "cover_letter_generated": ActivityType.COVER_LETTER_GENERATED.value,
        }
        return mapping.get(notification_type, ActivityType.LOGIN.value)

    def _map_notification_type_to_entity_type(self, notification_type: str) -> str:
        mapping = {
            "resume_uploaded": EntityType.RESUME.value,
            "resume_analysis_completed": EntityType.ANALYSIS.value,
            "job_analysis_completed": EntityType.JOB.value,
            "resume_tailoring_completed": EntityType.TAILORING.value,
            "cover_letter_generated": EntityType.COVER_LETTER.value,
        }
        return mapping.get(notification_type, EntityType.EXPORT.value)

    def _build_quick_actions(
        self,
        *,
        total_resumes: int,
        has_resume_analysis: bool,
        has_job_analysis: bool,
        average_ats_score: float | None,
        has_unread_notifications: bool,
        has_missing_skills: bool,
    ) -> list[DashboardQuickActionResponse]:
        actions: list[DashboardQuickActionResponse] = []

        if total_resumes == 0:
            actions.append(
                DashboardQuickActionResponse(
                    key="upload_resume",
                    title="Upload resume",
                    description="Add a resume to start receiving AI insights.",
                    route="/resumes/upload",
                    priority=1,
                )
            )

        if total_resumes > 0 and not has_resume_analysis:
            actions.append(
                DashboardQuickActionResponse(
                    key="run_resume_analysis",
                    title="Analyze your resume",
                    description="Run ATS analysis to generate improvement suggestions.",
                    route="/analysis",
                    priority=1,
                )
            )

        if total_resumes > 0 and not has_job_analysis:
            actions.append(
                DashboardQuickActionResponse(
                    key="analyze_job_match",
                    title="Analyze against a job",
                    description="Compare your resume with a job description.",
                    route="/job-analysis",
                    priority=2,
                )
            )

        if average_ats_score is not None and average_ats_score < 75:
            actions.append(
                DashboardQuickActionResponse(
                    key="improve_ats",
                    title="Improve ATS score",
                    description="Use resume tailoring to raise ATS performance.",
                    route="/resume-tailoring",
                    priority=2,
                )
            )

        if has_missing_skills:
            actions.append(
                DashboardQuickActionResponse(
                    key="close_skill_gaps",
                    title="Address missing skills",
                    description="Update your resume to cover missing requirements.",
                    route="/job-analysis",
                    priority=3,
                )
            )

        if has_unread_notifications:
            actions.append(
                DashboardQuickActionResponse(
                    key="review_notifications",
                    title="Review unread activity",
                    description="Check recent dashboard updates and events.",
                    route="/",
                    priority=4,
                )
            )

        actions.sort(key=lambda item: item.priority)
        return actions
