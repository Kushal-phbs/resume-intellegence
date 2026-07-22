"""Business logic for user dashboard analytics."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.config import settings
from app.dto.analytics import (
    ActivityDTO,
    AnalyticsDTO,
    DashboardDTO,
    DashboardSummaryDTO,
)
from app.enums.analytics import ActivityType, EntityType
from app.repositories.activity_repository import ActivityRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.services.cache_service import CacheService


class DashboardService:
    """Coordinates dashboard snapshots, analytics counters, and activity history."""

    def __init__(
        self,
        dashboard_repository: DashboardRepository,
        analytics_repository: AnalyticsRepository,
        activity_repository: ActivityRepository,
        cache_service: CacheService | None = None,
    ) -> None:
        self._dashboards = dashboard_repository
        self._analytics = analytics_repository
        self._activities = activity_repository
        self._cache = cache_service

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
            cached = await self._cache.get(
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
            await self._cache.set(
                namespace=self._summary_namespace(user_id),
                key=f"limit:{activity_limit}",
                value=summary.model_dump(mode="json"),
                ttl_seconds=settings.cache_dashboard_summary_ttl_seconds,
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
            cached = await self._cache.get(
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
            await self._cache.set(
                namespace=self._statistics_namespace(user_id),
                key="current",
                value=result,
                ttl_seconds=settings.cache_dashboard_statistics_ttl_seconds,
            )
        return result

    async def get_trends(
        self,
        *,
        user_id: UUID,
        points: int = 12,
    ) -> list[dict[str, float | int | datetime | None]]:
        if self._cache is not None:
            cached = await self._cache.get(
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
            await self._cache.set(
                namespace=self._trends_namespace(user_id),
                key=f"points:{points}",
                value=trend_points,
                ttl_seconds=settings.cache_dashboard_trends_ttl_seconds,
            )
        return trend_points

    async def get_performance(
        self,
        *,
        user_id: UUID,
    ) -> dict[str, float | int | UUID | datetime | None]:
        if self._cache is not None:
            cached = await self._cache.get(
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
                await self._cache.set(
                    namespace=self._performance_namespace(user_id),
                    key="current",
                    value=empty_result,
                    ttl_seconds=settings.cache_dashboard_performance_ttl_seconds,
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
            await self._cache.set(
                namespace=self._performance_namespace(user_id),
                key="current",
                value=result,
                ttl_seconds=settings.cache_dashboard_performance_ttl_seconds,
            )
        return result

    async def _invalidate_dashboard_cache(self, user_id: UUID) -> None:
        if self._cache is None:
            return
        await self._cache.invalidate(self._summary_namespace(user_id))
        await self._cache.invalidate(self._statistics_namespace(user_id))
        await self._cache.invalidate(self._trends_namespace(user_id))
        await self._cache.invalidate(self._performance_namespace(user_id))

    def _summary_namespace(self, user_id: UUID) -> str:
        return f"dashboard_summary:{user_id}"

    def _statistics_namespace(self, user_id: UUID) -> str:
        return f"dashboard_statistics:{user_id}"

    def _trends_namespace(self, user_id: UUID) -> str:
        return f"dashboard_trends:{user_id}"

    def _performance_namespace(self, user_id: UUID) -> str:
        return f"dashboard_performance:{user_id}"

    def _round_average(self, value: object) -> float | None:
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
