"""Business logic orchestration for resume intelligence analysis."""

from __future__ import annotations

from uuid import UUID

from app.config import settings
from app.core.exceptions import (
    ExternalServiceException,
    ResumeNotFoundException,
    ValidationException,
)
from app.dto.analysis import AnalysisResult
from app.enums import AnalysisStatus
from app.extractors.factory import TextExtractorFactory
from app.llm.models import LLMRequest
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.resume_version import ResumeVersion
from app.parsers.analysis_parser import AnalysisParser
from app.prompts.ats import AtsPrompt
from app.prompts.keywords import KeywordPrompt
from app.prompts.resume_parser import ResumeParserPrompt
from app.prompts.resume_review import ResumeReviewPrompt
from app.prompts.skills import SkillPrompt
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.analysis import (
    KeywordResponse,
    ResumeAnalysisResponse,
    ResumeAnalysisSummaryResponse,
    SkillResponse,
)
from app.services.cache_service import CacheService
from app.services.chat_service import ChatService
from app.storage.base import StorageProvider


class ResumeAnalysisService:
    """Coordinates resume retrieval, typed parsing, and persistence.

    The service owns all orchestration concerns, while parsing and text
    extraction are delegated to dedicated components.
    """

    def __init__(
        self,
        analysis_repository: ResumeAnalysisRepository,
        resume_repository: ResumeRepository,
        storage_provider: StorageProvider,
        chat_service: ChatService,
        analysis_parser: AnalysisParser | None = None,
        extractor_factory: TextExtractorFactory | None = None,
        cache_service: CacheService | None = None,
    ) -> None:
        self._analysis_repository = analysis_repository
        self._resume_repository = resume_repository
        self._storage = storage_provider
        self._chat_service = chat_service
        self._analysis_parser = analysis_parser or AnalysisParser()
        self._extractor_factory = extractor_factory or TextExtractorFactory()
        self._cache = cache_service

    async def analyze_resume(
        self, user_id: UUID, resume_id: UUID
    ) -> ResumeAnalysisResponse:
        """Analyze the latest uploaded version of a resume and persist results."""
        resume = await self._get_owned_resume(user_id=user_id, resume_id=resume_id)
        resume_version = await self._get_latest_version(resume_id)
        active_analysis = await self._analysis_repository.get_active_by_resume(
            resume_id
        )
        if active_analysis is not None:
            raise ValidationException(
                "An analysis is already in progress for this resume",
                status_code=409,
            )
        content = self._read_resume_bytes(resume_version)
        extractor = self._extractor_factory.get_extractor(
            resume_version.file_path or ""
        )
        extracted_text = extractor.extract(content)
        if not extracted_text.strip():
            raise ValidationException("Resume file is empty")

        analysis = await self._analysis_repository.create(
            resume_id=resume.id,
            resume_version_id=resume_version.id,
            analysis_status=AnalysisStatus.PROCESSING,
            extracted_text=extracted_text,
        )

        llm_response = None
        try:
            llm_response = await self._chat_service.chat(
                LLMRequest(
                    system_prompt=self._build_system_prompt(),
                    prompt=extracted_text,
                    temperature=0.2,
                    max_tokens=2048,
                )
            )
            result = self._analysis_parser.parse(llm_response.content)
            updated = await self._analysis_repository.update(
                analysis.id,
                result=result,
                analysis_status=AnalysisStatus.COMPLETED,
                llm_model=llm_response.model,
                raw_response=llm_response.content,
                error_message=None,
            )
        except Exception as exc:
            failed_result = AnalysisResult(ats_score=0)
            failed = await self._analysis_repository.update(
                analysis.id,
                result=failed_result,
                analysis_status=AnalysisStatus.FAILED,
                llm_model=llm_response.model if llm_response is not None else None,
                raw_response=llm_response.content if llm_response is not None else None,
                error_message=str(exc),
            )
            if failed is None:
                raise ExternalServiceException("Analysis persistence failed") from exc
            raise

        if updated is None:
            raise ExternalServiceException("Analysis persistence failed")

        await self._invalidate_resume_cache(user_id=user_id, resume_id=resume_id)
        return self._to_response(updated)

    async def get_latest_analysis(
        self, user_id: UUID, resume_id: UUID
    ) -> ResumeAnalysisResponse:
        """Return the newest completed analysis stored for a resume."""
        if self._cache is not None:
            cached = await self._cache.get(
                namespace=self._cache_namespace(user_id, resume_id),
                key="latest",
            )
            if cached is not None:
                return ResumeAnalysisResponse.model_validate(cached)

        analysis = await self._get_latest_completed_analysis(user_id, resume_id)
        response = self._to_response(analysis)
        if self._cache is not None:
            await self._cache.set(
                namespace=self._cache_namespace(user_id, resume_id),
                key="latest",
                value=response.model_dump(mode="json"),
                ttl_seconds=settings.cache_resume_analysis_ttl_seconds,
            )
        return response

    async def get_latest_summary(
        self, user_id: UUID, resume_id: UUID
    ) -> ResumeAnalysisSummaryResponse:
        """Return the latest completed analysis summary for a resume."""
        if self._cache is not None:
            cached = await self._cache.get(
                namespace=self._cache_namespace(user_id, resume_id),
                key="summary",
            )
            if cached is not None:
                return ResumeAnalysisSummaryResponse.model_validate(cached)

        analysis = await self._get_latest_completed_analysis(user_id, resume_id)
        response = self._to_summary(analysis)
        if self._cache is not None:
            await self._cache.set(
                namespace=self._cache_namespace(user_id, resume_id),
                key="summary",
                value=response.model_dump(mode="json"),
                ttl_seconds=settings.cache_resume_analysis_ttl_seconds,
            )
        return response

    async def get_latest_skills(
        self, user_id: UUID, resume_id: UUID
    ) -> list[SkillResponse]:
        """Return the extracted skills from the latest completed analysis."""
        analysis = await self._get_latest_completed_analysis(user_id, resume_id)
        return [SkillResponse.model_validate(skill) for skill in analysis.skills]

    async def get_latest_keywords(
        self, user_id: UUID, resume_id: UUID
    ) -> list[KeywordResponse]:
        """Return the extracted keywords from the latest completed analysis."""
        analysis = await self._get_latest_completed_analysis(user_id, resume_id)
        return [
            KeywordResponse.model_validate(keyword) for keyword in analysis.keywords
        ]

    async def list_analyses(
        self, user_id: UUID, resume_id: UUID
    ) -> list[ResumeAnalysisSummaryResponse]:
        """Return all stored analyses for a resume."""
        await self._get_owned_resume(user_id=user_id, resume_id=resume_id)
        analyses = await self._analysis_repository.list_by_resume(resume_id)
        return [self._to_summary(analysis) for analysis in analyses]

    async def delete_analysis(self, user_id: UUID, analysis_id: UUID) -> None:
        """Delete a stored analysis by UUID when it belongs to the user."""
        analysis = await self._analysis_repository.get_by_id(analysis_id)
        if analysis is None or analysis.resume.user_id != user_id:
            raise ResumeNotFoundException("Analysis not found")
        deleted = await self._analysis_repository.delete(analysis_id)
        if not deleted:
            raise ResumeNotFoundException("Analysis not found")
        await self._invalidate_resume_cache(
            user_id=user_id,
            resume_id=analysis.resume_id,
        )

    async def _invalidate_resume_cache(self, *, user_id: UUID, resume_id: UUID) -> None:
        if self._cache is None:
            return
        await self._cache.invalidate(self._cache_namespace(user_id, resume_id))

    def _cache_namespace(self, user_id: UUID, resume_id: UUID) -> str:
        return f"resume_analysis:{user_id}:{resume_id}"

    async def _get_owned_resume(self, *, user_id: UUID, resume_id: UUID) -> Resume:
        resume = await self._resume_repository.get(resume_id)
        if resume is None or resume.user_id != user_id:
            raise ResumeNotFoundException()
        return resume

    async def _get_latest_version(self, resume_id: UUID) -> ResumeVersion:
        version = await self._resume_repository.get_latest_version(resume_id)
        if version is None or not version.file_path:
            raise ResumeNotFoundException("Resume content not found")
        return version

    def _read_resume_bytes(self, version: ResumeVersion) -> bytes:
        if not version.file_path:
            raise ResumeNotFoundException("Resume content not found")
        return self._storage.read(version.file_path)

    def _build_system_prompt(self) -> str:
        prompts = [
            ResumeParserPrompt().build(),
            AtsPrompt().build(),
            SkillPrompt().build(),
            KeywordPrompt().build(),
            ResumeReviewPrompt().build(),
            (
                "Return valid JSON only with keys: resume_score, ats_score, "
                "strengths, weaknesses, recommendations, skills, keywords. "
                "Each skill must include skill_name and category."
            ),
        ]
        return "\n\n".join(prompts)

    def _to_response(self, analysis: ResumeAnalysis) -> ResumeAnalysisResponse:
        return ResumeAnalysisResponse(
            id=analysis.id,
            resume_id=analysis.resume_id,
            resume_version_id=analysis.resume_version_id,
            analysis_status=AnalysisStatus(analysis.analysis_status),
            resume_score=analysis.resume_score,
            ats_score=analysis.ats_score,
            strengths=analysis.strengths,
            weaknesses=analysis.weaknesses,
            recommendations=analysis.recommendations,
            skills=[SkillResponse.model_validate(skill) for skill in analysis.skills],
            keywords=[
                KeywordResponse.model_validate(keyword) for keyword in analysis.keywords
            ],
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            error_message=analysis.error_message,
        )

    def _to_summary(self, analysis: ResumeAnalysis) -> ResumeAnalysisSummaryResponse:
        return ResumeAnalysisSummaryResponse(
            id=analysis.id,
            resume_id=analysis.resume_id,
            resume_version_id=analysis.resume_version_id,
            analysis_status=AnalysisStatus(analysis.analysis_status),
            resume_score=analysis.resume_score,
            ats_score=analysis.ats_score,
            strengths=analysis.strengths,
            weaknesses=analysis.weaknesses,
            recommendations=analysis.recommendations,
            skill_count=len(analysis.skills),
            keyword_count=len(analysis.keywords),
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            error_message=analysis.error_message,
        )

    async def _get_latest_completed_analysis(
        self, user_id: UUID, resume_id: UUID
    ) -> ResumeAnalysis:
        await self._get_owned_resume(user_id=user_id, resume_id=resume_id)
        analysis = await self._analysis_repository.get_latest_completed(resume_id)
        if analysis is None:
            raise ResumeNotFoundException("Analysis not found")
        return analysis
