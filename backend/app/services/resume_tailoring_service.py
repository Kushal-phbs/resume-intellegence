"""Business logic orchestration for AI resume tailoring."""

from __future__ import annotations

from uuid import UUID

import anyio

from app.core.exceptions import (
    ExternalServiceException,
    ResourceNotFoundException,
    ResumeNotFoundException,
    ValidationException,
)
from app.dto.tailoring import (
    CoverLetterDTO,
    ResumeTailoringDTO,
    ResumeVersionDTO,
    TailoringSessionDTO,
)
from app.enums.tailoring import TailoringStatus
from app.extractors.factory import TextExtractorFactory
from app.llm.models import LLMRequest
from app.models.cover_letter import CoverLetter
from app.models.resume import Resume
from app.models.resume_tailoring_version import ResumeTailoringVersion
from app.models.resume_version import ResumeVersion
from app.models.tailoring_session import TailoringSession
from app.parsers.tailoring_parser import TailoringParser
from app.prompts.cover_letter_builder import CoverLetterPrompt
from app.prompts.resume_rewrite import ResumeRewritePrompt
from app.prompts.tailoring_ats import TailoringAtsPrompt
from app.repositories.cover_letter_repository import CoverLetterRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.resume_version_repository import ResumeVersionRepository
from app.repositories.tailoring_session_repository import TailoringSessionRepository
from app.schemas.notification import NotificationCreate
from app.services.chat_service import ChatService
from app.services.notification_service import NotificationService
from app.storage.base import StorageProvider


class ResumeTailoringService:
    """Coordinates ownership checks, prompting, parsing, and persistence."""

    def __init__(
        self,
        tailoring_session_repository: TailoringSessionRepository,
        resume_version_repository: ResumeVersionRepository,
        cover_letter_repository: CoverLetterRepository,
        resume_repository: ResumeRepository,
        job_description_repository: JobDescriptionRepository,
        storage_provider: StorageProvider,
        chat_service: ChatService,
        notification_service: NotificationService | None = None,
        parser: TailoringParser | None = None,
        extractor_factory: TextExtractorFactory | None = None,
    ) -> None:
        self._tailoring_sessions = tailoring_session_repository
        self._resume_versions = resume_version_repository
        self._cover_letters = cover_letter_repository
        self._resumes = resume_repository
        self._job_descriptions = job_description_repository
        self._storage = storage_provider
        self._chat_service = chat_service
        self._notifications = notification_service
        self._parser = parser or TailoringParser()
        self._extractor_factory = extractor_factory or TextExtractorFactory()

    async def tailor_resume(
        self,
        *,
        user_id: UUID,
        resume_id: UUID,
        job_description_id: UUID,
    ) -> ResumeTailoringDTO:
        """Generate tailored resume content and a cover letter for one job."""
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

        session = await self._tailoring_sessions.create(
            resume_id=resume.id,
            job_description_id=job_description.id,
            status=TailoringStatus.PROCESSING,
        )

        try:
            response = await self._chat_service.chat(
                LLMRequest(
                    system_prompt=self._build_system_prompt(),
                    prompt=self._build_user_prompt(
                        resume_text=resume_text,
                        job_description_text=job_text,
                    ),
                    temperature=0.2,
                    max_tokens=3072,
                )
            )
            parsed = self._parser.parse(response.content)

            persisted_version = await self._resume_versions.create(
                resume_id=resume.id,
                tailoring_session_id=session.id,
                professional_summary=parsed.resume_version.professional_summary,
                experience_json=parsed.resume_version.experience_json,
                skills_json=parsed.resume_version.skills_json,
                ats_score=parsed.resume_version.ats_score,
                recommendations_json=parsed.resume_version.recommendations_json,
            )
            persisted_letter = await self._cover_letters.create(
                tailoring_session_id=session.id,
                title=parsed.cover_letter.title,
                greeting=parsed.cover_letter.greeting,
                introduction=parsed.cover_letter.introduction,
                body=parsed.cover_letter.body,
                closing=parsed.cover_letter.closing,
            )
            updated_session = await self._tailoring_sessions.update(
                session.id,
                status=TailoringStatus.COMPLETED,
            )
            if updated_session is None:
                raise ExternalServiceException("Tailoring session persistence failed")
        except Exception:
            failed = await self._tailoring_sessions.update(
                session.id,
                status=TailoringStatus.FAILED,
            )
            if failed is None:
                raise ExternalServiceException("Tailoring session persistence failed")
            raise

        if self._notifications is not None:
            await self._notifications.create_notification(
                user_id=user_id,
                payload=NotificationCreate(
                    title="Resume tailoring complete",
                    message="Your tailored resume has been generated successfully.",
                    type="resume_tailoring_completed",
                    priority="high",
                    action_url=f"/resume-tailoring/{updated_session.id}/resume",
                    metadata_json={
                        "resume_id": str(resume_id),
                        "tailoring_session_id": str(updated_session.id),
                        "entity_id": str(updated_session.id),
                    },
                ),
            )
            await self._notifications.create_notification(
                user_id=user_id,
                payload=NotificationCreate(
                    title="Cover letter generated",
                    message="A personalized cover letter is ready.",
                    type="cover_letter_generated",
                    priority="medium",
                    action_url=f"/resume-tailoring/{updated_session.id}/cover-letter",
                    metadata_json={
                        "resume_id": str(resume_id),
                        "tailoring_session_id": str(updated_session.id),
                        "entity_id": str(updated_session.id),
                    },
                ),
            )

        return ResumeTailoringDTO(
            session=self._to_session_dto(updated_session),
            resume_version=self._to_resume_version_dto(persisted_version),
            cover_letter=self._to_cover_letter_dto(persisted_letter),
        )

    async def list_history(self, *, user_id: UUID) -> list[TailoringSessionDTO]:
        sessions = await self._tailoring_sessions.list_by_user(user_id)
        return [self._to_session_dto(session) for session in sessions]

    async def get_session(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
    ) -> TailoringSessionDTO:
        session = await self._get_owned_session(user_id=user_id, session_id=session_id)
        return self._to_session_dto(session)

    async def get_resume_version(
        self, *, user_id: UUID, session_id: UUID
    ) -> ResumeVersionDTO:
        await self._get_owned_session(user_id=user_id, session_id=session_id)
        version = await self._resume_versions.get_by_session(session_id)
        if version is None:
            raise ResourceNotFoundException("Tailored resume version not found")
        return self._to_resume_version_dto(version)

    async def get_cover_letter(
        self, *, user_id: UUID, session_id: UUID
    ) -> CoverLetterDTO:
        await self._get_owned_session(user_id=user_id, session_id=session_id)
        letter = await self._cover_letters.get_by_session(session_id)
        if letter is None:
            raise ResourceNotFoundException("Cover letter not found")
        return self._to_cover_letter_dto(letter)

    async def delete_session(self, *, user_id: UUID, session_id: UUID) -> None:
        session = await self._get_owned_session(user_id=user_id, session_id=session_id)
        deleted = await self._tailoring_sessions.delete(session_id, session=session)
        if not deleted:
            raise ResourceNotFoundException("Tailoring session not found")

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
    ):
        job_description = await self._job_descriptions.get(job_description_id)
        if job_description is None or job_description.user_id != user_id:
            raise ResourceNotFoundException("Job description not found")
        return job_description

    async def _extract_resume_text(self, version: ResumeVersion) -> str:
        if not version.file_path:
            raise ResumeNotFoundException("Resume content not found")

        def _read_and_extract() -> str:
            content = self._storage.read(version.file_path)
            extractor = self._extractor_factory.get_extractor(version.file_path)
            return extractor.extract(content)

        return await anyio.to_thread.run_sync(_read_and_extract)

    async def _get_owned_session(
        self, *, user_id: UUID, session_id: UUID
    ) -> TailoringSession:
        session = await self._tailoring_sessions.get_by_id(session_id)
        if session is None or session.resume.user_id != user_id:
            raise ResourceNotFoundException("Tailoring session not found")
        return session

    def _build_system_prompt(self) -> str:
        prompts = [
            ResumeRewritePrompt().build(),
            CoverLetterPrompt().build(),
            TailoringAtsPrompt().build(),
            (
                "Return ONLY valid JSON with this exact schema: "
                "{"
                '"professional_summary":"",'
                '"experience_json":[], '
                '"skills_json":[], '
                '"ats_score":0, '
                '"recommendations_json":[], '
                '"cover_letter":{'
                '"title":"",'
                '"greeting":"",'
                '"introduction":"",'
                '"body":"",'
                '"closing":""'
                "}"
                "}."
            ),
        ]
        return "\n\n".join(prompts)

    def _build_user_prompt(self, *, resume_text: str, job_description_text: str) -> str:
        return f"Resume:\n{resume_text}\n\nJob Description:\n{job_description_text}"

    def _to_session_dto(self, session: TailoringSession) -> TailoringSessionDTO:
        return TailoringSessionDTO(
            id=session.id,
            resume_id=session.resume_id,
            job_description_id=session.job_description_id,
            status=TailoringStatus(session.status),
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def _to_resume_version_dto(
        self, version: ResumeTailoringVersion
    ) -> ResumeVersionDTO:
        return ResumeVersionDTO(
            id=version.id,
            resume_id=version.resume_id,
            tailoring_session_id=version.tailoring_session_id,
            professional_summary=version.professional_summary,
            experience_json=version.experience_json,
            skills_json=version.skills_json,
            ats_score=version.ats_score,
            recommendations_json=version.recommendations_json,
            created_at=version.created_at,
            updated_at=version.updated_at,
        )

    def _to_cover_letter_dto(self, letter: CoverLetter) -> CoverLetterDTO:
        return CoverLetterDTO(
            id=letter.id,
            title=letter.title,
            greeting=letter.greeting,
            introduction=letter.introduction,
            body=letter.body,
            closing=letter.closing,
        )
