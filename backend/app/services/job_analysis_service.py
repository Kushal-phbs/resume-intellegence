"""Business logic orchestration for job intelligence analysis."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import anyio

from app.config import settings
from app.core.cache import RedisCache
from app.core.exceptions import (
    ExternalServiceException,
    ResourceNotFoundException,
    ResumeNotFoundException,
    ValidationException,
)
from app.core.logging import logger
from app.dto.job_analysis import JobAnalysisResult
from app.enums import JobAnalysisStatus
from app.extractors.factory import TextExtractorFactory
from app.llm.models import LLMRequest
from app.models.job_analysis import JobAnalysis
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.resume_version import ResumeVersion
from app.parsers.job_analysis_parser import JobAnalysisParser
from app.prompts.job_match import JobMatchPrompt
from app.prompts.keyword_match import KeywordMatchPrompt
from app.prompts.missing_skills import MissingSkillsPrompt
from app.prompts.recommendations import JobRecommendationsPrompt
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.job_analysis import (
    JobAnalysisResponse,
    JobAnalysisSummaryResponse,
    KeywordMatchResponse,
    MatchedSkillResponse,
    MissingSkillResponse,
)
from app.schemas.notification import NotificationCreate
from app.services.chat_service import ChatService
from app.services.notification_service import NotificationService
from app.storage.base import StorageProvider


class JobAnalysisService:
    """Coordinates resume/job retrieval, parsing, and persistence."""

    def __init__(
        self,
        job_analysis_repository: JobAnalysisRepository,
        resume_repository: ResumeRepository,
        job_description_repository: JobDescriptionRepository,
        storage_provider: StorageProvider,
        chat_service: ChatService,
        parser: JobAnalysisParser | None = None,
        extractor_factory: TextExtractorFactory | None = None,
        cache_service: Any | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self._job_analyses = job_analysis_repository
        self._resumes = resume_repository
        self._job_descriptions = job_description_repository
        self._storage = storage_provider
        self._chat_service = chat_service
        self._parser = parser or JobAnalysisParser()
        self._extractor_factory = extractor_factory or TextExtractorFactory()
        self._cache = cache_service or RedisCache(
            redis_url=settings.redis_url,
            default_ttl_seconds=settings.cache_default_ttl_seconds,
            enabled=settings.redis_enabled,
        )
        self._notifications = notification_service

    async def analyze_job_match(
        self,
        *,
        user_id: UUID,
        resume_id: UUID,
        job_description_id: UUID,
    ) -> JobAnalysisResponse:
        """Analyze resume fit against a job description and persist results."""
        resume = await self._get_owned_resume(user_id=user_id, resume_id=resume_id)
        resume_version = await self._get_latest_resume_version(resume_id)
        job_description = await self._get_owned_job_description(
            user_id=user_id,
            job_description_id=job_description_id,
        )

        resume_text = await self._extract_resume_text(resume_version)
        if not resume_text.strip():
            raise ValidationException("Resume file is empty")

        job_text = job_description.description.strip()
        if not job_text:
            raise ValidationException("Job description is empty")

        analysis = await self._job_analyses.create(
            resume_id=resume.id,
            job_description_id=job_description.id,
            analysis_status=JobAnalysisStatus.PROCESSING,
        )

        llm_response = None
        try:
            llm_response = await self._chat_service.chat(
                LLMRequest(
                    system_prompt=self._build_system_prompt(),
                    prompt=self._build_user_prompt(
                        resume_text=resume_text,
                        job_description_text=job_text,
                    ),
                    temperature=0.2,
                    max_tokens=2048,
                )
            )
            result = self._parser.parse(llm_response.content)
            updated = await self._job_analyses.update(
                analysis.id,
                result=result,
                analysis_status=JobAnalysisStatus.COMPLETED,
                llm_model=llm_response.model,
                raw_response=llm_response.content,
                error_message=None,
            )
        except Exception as exc:
            failed_result = JobAnalysisResult(
                overall_match=0,
                ats_match=0,
                summary="Analysis failed",
            )
            await self._job_analyses.persist_failed_committed(
                analysis_id=analysis.id,
                resume_id=resume.id,
                job_description_id=job_description.id,
                result=failed_result,
                llm_model=llm_response.model if llm_response is not None else None,
                raw_response=llm_response.content if llm_response is not None else None,
                error_message=str(exc),
            )
            raise

        if updated is None:
            raise ExternalServiceException("Job analysis persistence failed")

        if self._notifications is not None:
            await self._notifications.create_notification(
                user_id=user_id,
                payload=NotificationCreate(
                    title="Job analysis complete",
                    message="Your resume-to-job match analysis is ready.",
                    type="job_analysis_completed",
                    priority="high",
                    action_url=f"/job-analysis/{updated.id}",
                    metadata_json={
                        "resume_id": str(resume_id),
                        "analysis_id": str(updated.id),
                        "entity_id": str(updated.id),
                    },
                ),
            )

        await self._invalidate_user_cache(user_id)
        return self._to_response(updated)

    async def get_analysis(
        self, *, user_id: UUID, analysis_id: UUID
    ) -> JobAnalysisResponse:
        """Return one job analysis owned by the requesting user."""
        if self._cache is not None:
            cached = await self._cache_get(
                namespace=self._analysis_namespace(user_id),
                key=str(analysis_id),
            )
            if cached is not None:
                return JobAnalysisResponse.model_validate(cached)

        analysis = await self._get_owned_analysis(
            user_id=user_id,
            analysis_id=analysis_id,
        )
        response = self._to_response(analysis)
        if self._cache is not None:
            await self._cache_set(
                namespace=self._analysis_namespace(user_id),
                key=str(analysis_id),
                value=response.model_dump(mode="json"),
                ttl_seconds=self._ttl_seconds(settings.cache_job_analysis_ttl_seconds),
            )
        return response

    async def get_summary(
        self, *, user_id: UUID, analysis_id: UUID
    ) -> JobAnalysisSummaryResponse:
        """Return summary fields for a job analysis owned by the user."""
        if self._cache is not None:
            cached = await self._cache_get(
                namespace=self._summary_namespace(user_id),
                key=str(analysis_id),
            )
            if cached is not None:
                return JobAnalysisSummaryResponse.model_validate(cached)

        analysis = await self._get_owned_analysis(
            user_id=user_id,
            analysis_id=analysis_id,
        )
        response = self._to_summary(analysis)
        if self._cache is not None:
            await self._cache_set(
                namespace=self._summary_namespace(user_id),
                key=str(analysis_id),
                value=response.model_dump(mode="json"),
                ttl_seconds=self._ttl_seconds(settings.cache_job_analysis_ttl_seconds),
            )
        return response

    async def get_matched_skills(
        self, *, user_id: UUID, analysis_id: UUID
    ) -> list[MatchedSkillResponse]:
        """Return matched skills for one owned job analysis."""
        analysis = await self._get_owned_analysis(
            user_id=user_id,
            analysis_id=analysis_id,
        )
        return [
            MatchedSkillResponse.model_validate(skill)
            for skill in analysis.matched_skills
        ]

    async def get_missing_skills(
        self, *, user_id: UUID, analysis_id: UUID
    ) -> list[MissingSkillResponse]:
        """Return missing skills for one owned job analysis."""
        analysis = await self._get_owned_analysis(
            user_id=user_id,
            analysis_id=analysis_id,
        )
        return [
            MissingSkillResponse.model_validate(skill)
            for skill in analysis.missing_skills
        ]

    async def get_keyword_matches(
        self, *, user_id: UUID, analysis_id: UUID
    ) -> list[KeywordMatchResponse]:
        """Return keyword matches for one owned job analysis."""
        analysis = await self._get_owned_analysis(
            user_id=user_id,
            analysis_id=analysis_id,
        )
        return [
            KeywordMatchResponse.model_validate(keyword)
            for keyword in analysis.keyword_matches
        ]

    async def list_history(self, *, user_id: UUID) -> list[JobAnalysisSummaryResponse]:
        """Return previous job analyses for the authenticated user."""
        if self._cache is not None:
            cached = await self._cache_get(
                namespace=self._history_namespace(user_id),
                key="latest",
            )
            if cached is not None:
                return [
                    JobAnalysisSummaryResponse.model_validate(item) for item in cached
                ]

        analyses = await self._job_analyses.list_history_by_user(user_id)
        summaries = [self._to_summary(analysis) for analysis in analyses]
        if self._cache is not None:
            await self._cache_set(
                namespace=self._history_namespace(user_id),
                key="latest",
                value=[item.model_dump(mode="json") for item in summaries],
                ttl_seconds=self._ttl_seconds(settings.cache_job_analysis_ttl_seconds),
            )
        return summaries

    async def delete_analysis(self, *, user_id: UUID, analysis_id: UUID) -> None:
        """Delete one job analysis when it belongs to the user."""
        analysis = await self._get_owned_analysis(
            user_id=user_id,
            analysis_id=analysis_id,
        )
        deleted = await self._job_analyses.delete(analysis_id, analysis=analysis)
        if not deleted:
            raise ResourceNotFoundException("Job analysis not found")
        await self._invalidate_user_cache(user_id)

    async def _invalidate_user_cache(self, user_id: UUID) -> None:
        if self._cache is None:
            return
        await self._cache_delete_pattern(self._analysis_pattern(user_id))
        await self._cache_delete_pattern(self._summary_pattern(user_id))
        await self._cache_delete_pattern(self._history_pattern(user_id))

    def _analysis_namespace(self, user_id: UUID) -> str:
        return f"job_analysis:detail:{user_id}"

    def _analysis_pattern(self, user_id: UUID) -> str:
        return f"{self._analysis_namespace(user_id)}:*"

    def _summary_namespace(self, user_id: UUID) -> str:
        return f"job_analysis:summary:{user_id}"

    def _summary_pattern(self, user_id: UUID) -> str:
        return f"{self._summary_namespace(user_id)}:*"

    def _history_namespace(self, user_id: UUID) -> str:
        return f"job_analysis:history:{user_id}"

    def _history_pattern(self, user_id: UUID) -> str:
        return f"{self._history_namespace(user_id)}:*"

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

    async def _get_owned_resume(self, *, user_id: UUID, resume_id: UUID) -> Resume:
        resume = await self._resumes.get(resume_id)
        if resume is None or resume.user_id != user_id:
            raise ResumeNotFoundException()
        return resume

    async def _get_latest_resume_version(self, resume_id: UUID) -> ResumeVersion:
        version = await self._resumes.get_latest_version(resume_id)
        if version is None or not version.file_path:
            raise ResumeNotFoundException("Resume content not found")
        return version

    async def _get_owned_job_description(
        self,
        *,
        user_id: UUID,
        job_description_id: UUID,
    ) -> JobDescription:
        job_description = await self._job_descriptions.get(job_description_id)
        if job_description is None or job_description.user_id != user_id:
            raise ResourceNotFoundException("Job description not found")
        return job_description

    async def _extract_resume_text(self, resume_version: ResumeVersion) -> str:
        if not resume_version.file_path:
            raise ResumeNotFoundException("Resume content not found")

        def _read_and_extract() -> str:
            content = self._storage.read(resume_version.file_path)
            extractor = self._extractor_factory.get_extractor(resume_version.file_path)
            return extractor.extract(content)

        return await anyio.to_thread.run_sync(_read_and_extract)

    def _build_system_prompt(self) -> str:
        prompts = [
            JobMatchPrompt().build(),
            MissingSkillsPrompt().build(),
            KeywordMatchPrompt().build(),
            JobRecommendationsPrompt().build(),
            (
                "Return ONLY valid JSON. Do not include markdown, code fences, "
                "or explanations. Use exactly this schema and keys:\n"
                "{\n"
                '  "overall_match": 0,\n'
                '  "ats_match": 0,\n'
                '  "summary": "",\n'
                '  "matched_skills": [],\n'
                '  "missing_skills": [],\n'
                '  "keyword_matches": [],\n'
                '  "strengths": [],\n'
                '  "weaknesses": [],\n'
                '  "recommendations": []\n'
                "}"
            ),
        ]
        return "\n\n".join(prompts)

    def _build_user_prompt(self, *, resume_text: str, job_description_text: str) -> str:
        return f"Resume:\n{resume_text}\n\nJob Description:\n{job_description_text}"

    async def _get_owned_analysis(
        self, *, user_id: UUID, analysis_id: UUID
    ) -> JobAnalysis:
        analysis = await self._job_analyses.get_by_id(analysis_id)
        if analysis is None or analysis.resume.user_id != user_id:
            raise ResourceNotFoundException("Job analysis not found")
        return analysis

    def _to_response(self, analysis: JobAnalysis) -> JobAnalysisResponse:
        return JobAnalysisResponse(
            id=analysis.id,
            resume_id=analysis.resume_id,
            job_description_id=analysis.job_description_id,
            analysis_status=JobAnalysisStatus(analysis.analysis_status),
            match_score=analysis.match_score,
            ats_match_score=analysis.ats_match_score,
            summary=analysis.summary,
            strengths=analysis.strengths,
            weaknesses=analysis.weaknesses,
            recommendations=analysis.recommendations,
            matched_skills=[
                MatchedSkillResponse.model_validate(skill)
                for skill in analysis.matched_skills
            ],
            missing_skills=[
                MissingSkillResponse.model_validate(skill)
                for skill in analysis.missing_skills
            ],
            keyword_matches=[
                KeywordMatchResponse.model_validate(keyword)
                for keyword in analysis.keyword_matches
            ],
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            error_message=analysis.error_message,
        )

    def _to_summary(self, analysis: JobAnalysis) -> JobAnalysisSummaryResponse:
        return JobAnalysisSummaryResponse(
            id=analysis.id,
            resume_id=analysis.resume_id,
            job_description_id=analysis.job_description_id,
            analysis_status=JobAnalysisStatus(analysis.analysis_status),
            match_score=analysis.match_score,
            ats_match_score=analysis.ats_match_score,
            strengths=analysis.strengths,
            weaknesses=analysis.weaknesses,
            recommendations=analysis.recommendations,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            error_message=analysis.error_message,
        )
