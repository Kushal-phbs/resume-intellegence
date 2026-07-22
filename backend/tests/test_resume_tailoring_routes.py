from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.resume_tailoring import export_router
from app.api.routes.resume_tailoring import router as tailoring_router
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.core.handlers import register_exception_handlers
from app.dependencies.auth import get_current_user
from app.dependencies.resume_tailoring import (
    get_export_service,
    get_resume_tailoring_service,
)
from app.dto.tailoring import (
    CoverLetterDTO,
    ResumeTailoringDTO,
    ResumeVersionDTO,
    TailoringSessionDTO,
)
from app.enums.tailoring import TailoringStatus


class _TailoringServiceStub:
    def __init__(self, owner_id: UUID) -> None:
        self.owner_id = owner_id
        self.calls: list[tuple[str, UUID]] = []
        self.session = _session_dto()
        self.resume_version = _resume_version_dto(
            self.session.id,
            self.session.resume_id,
        )
        self.cover_letter = _cover_letter_dto()
        self.missing = False

    async def tailor_resume(
        self,
        *,
        user_id: UUID,
        resume_id: UUID,
        job_description_id: UUID,
    ) -> ResumeTailoringDTO:
        self.calls.append(("tailor_resume", user_id))
        self._assert_owner(user_id)
        if self.missing:
            raise ResourceNotFoundException("Resume not found")
        return ResumeTailoringDTO(
            session=TailoringSessionDTO(
                id=self.session.id,
                resume_id=resume_id,
                job_description_id=job_description_id,
                status=TailoringStatus.COMPLETED,
                created_at=self.session.created_at,
                updated_at=self.session.updated_at,
            ),
            resume_version=ResumeVersionDTO(
                id=self.resume_version.id,
                resume_id=resume_id,
                tailoring_session_id=self.session.id,
                professional_summary=self.resume_version.professional_summary,
                experience_json=self.resume_version.experience_json,
                skills_json=self.resume_version.skills_json,
                ats_score=self.resume_version.ats_score,
                recommendations_json=self.resume_version.recommendations_json,
                created_at=self.resume_version.created_at,
                updated_at=self.resume_version.updated_at,
            ),
            cover_letter=self.cover_letter,
        )

    async def list_history(self, *, user_id: UUID) -> list[TailoringSessionDTO]:
        self.calls.append(("list_history", user_id))
        self._assert_owner(user_id)
        return [self.session]

    async def get_session(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
    ) -> TailoringSessionDTO:
        self.calls.append(("get_session", user_id))
        self._assert_owner(user_id)
        if self.missing:
            raise ResourceNotFoundException("Tailoring session not found")
        return TailoringSessionDTO(
            id=session_id,
            resume_id=self.session.resume_id,
            job_description_id=self.session.job_description_id,
            status=self.session.status,
            created_at=self.session.created_at,
            updated_at=self.session.updated_at,
        )

    async def get_resume_version(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
    ) -> ResumeVersionDTO:
        self.calls.append(("get_resume_version", user_id))
        self._assert_owner(user_id)
        if self.missing:
            raise ResourceNotFoundException("Tailored resume version not found")
        return ResumeVersionDTO(
            id=self.resume_version.id,
            resume_id=self.session.resume_id,
            tailoring_session_id=session_id,
            professional_summary=self.resume_version.professional_summary,
            experience_json=self.resume_version.experience_json,
            skills_json=self.resume_version.skills_json,
            ats_score=self.resume_version.ats_score,
            recommendations_json=self.resume_version.recommendations_json,
            created_at=self.resume_version.created_at,
            updated_at=self.resume_version.updated_at,
        )

    async def get_cover_letter(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
    ) -> CoverLetterDTO:
        self.calls.append(("get_cover_letter", user_id))
        self._assert_owner(user_id)
        if self.missing:
            raise ResourceNotFoundException("Cover letter not found")
        _ = session_id
        return self.cover_letter

    async def delete_session(self, *, user_id: UUID, session_id: UUID) -> None:
        self.calls.append(("delete_session", user_id))
        self._assert_owner(user_id)
        _ = session_id
        if self.missing:
            raise ResourceNotFoundException("Tailoring session not found")

    def _assert_owner(self, user_id: UUID) -> None:
        if user_id != self.owner_id:
            raise ResourceNotFoundException("Tailoring session not found")


class _ExportServiceStub:
    def __init__(
        self,
        owner_id: UUID,
        resume_export_path: Path,
        letter_export_path: Path,
    ) -> None:
        self.owner_id = owner_id
        self.resume_export_path = resume_export_path
        self.letter_export_path = letter_export_path
        self.calls: list[tuple[str, UUID, str]] = []
        self.invalid_format = False
        self.missing = False

    async def export_resume(
        self,
        *,
        user_id: UUID,
        version_id: UUID,
        format: str,
    ) -> Path:
        self.calls.append(("export_resume", version_id, format))
        self._assert_owner(user_id)
        if self.missing:
            raise ResourceNotFoundException("Tailored resume version not found")
        if self.invalid_format:
            raise ValidationException("Unsupported export format")
        return self.resume_export_path

    async def export_cover_letter(
        self,
        *,
        user_id: UUID,
        cover_letter_id: UUID,
        format: str,
    ) -> Path:
        self.calls.append(("export_cover_letter", cover_letter_id, format))
        self._assert_owner(user_id)
        if self.missing:
            raise ResourceNotFoundException("Cover letter not found")
        if self.invalid_format:
            raise ValidationException("Unsupported export format")
        return self.letter_export_path

    def _assert_owner(self, user_id: UUID) -> None:
        if user_id != self.owner_id:
            raise ResourceNotFoundException("Export not found")


def _session_dto() -> TailoringSessionDTO:
    now = datetime.now(UTC)
    return TailoringSessionDTO(
        id=uuid4(),
        resume_id=uuid4(),
        job_description_id=uuid4(),
        status=TailoringStatus.COMPLETED,
        created_at=now,
        updated_at=now,
    )


def _resume_version_dto(session_id: UUID, resume_id: UUID) -> ResumeVersionDTO:
    now = datetime.now(UTC)
    return ResumeVersionDTO(
        id=uuid4(),
        resume_id=resume_id,
        tailoring_session_id=session_id,
        professional_summary="Tailored summary",
        experience_json=[{"text": "Led a migration"}],
        skills_json=[{"name": "Python"}],
        ats_score=92,
        recommendations_json=[{"text": "Add quantified impact"}],
        created_at=now,
        updated_at=now,
    )


def _cover_letter_dto() -> CoverLetterDTO:
    return CoverLetterDTO(
        title="Senior Backend Engineer",
        greeting="Dear Hiring Manager,",
        introduction="I am excited to apply for the role.",
        body="I have built resilient FastAPI services at scale.",
        closing="Sincerely, Candidate",
    )


def _build_app(
    tailoring_service_stub: _TailoringServiceStub,
    export_service_stub: _ExportServiceStub,
    current_user_id: UUID,
) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(tailoring_router)
    app.include_router(export_router)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=current_user_id
    )
    app.dependency_overrides[get_resume_tailoring_service] = lambda: (
        tailoring_service_stub
    )
    app.dependency_overrides[get_export_service] = lambda: export_service_stub
    return app


def _make_client(
    tailoring_service_stub: _TailoringServiceStub,
    export_service_stub: _ExportServiceStub,
    current_user_id: UUID,
) -> TestClient:
    return TestClient(
        _build_app(
            tailoring_service_stub=tailoring_service_stub,
            export_service_stub=export_service_stub,
            current_user_id=current_user_id,
        )
    )


def test_create_tailoring_session_success(tmp_path: Path) -> None:
    user_id = uuid4()
    service_stub = _TailoringServiceStub(owner_id=user_id)
    export_stub = _ExportServiceStub(
        owner_id=user_id,
        resume_export_path=tmp_path / "tailored.md",
        letter_export_path=tmp_path / "cover-letter.md",
    )
    client = _make_client(service_stub, export_stub, user_id)

    response = client.post(f"/resume-tailoring/{uuid4()}/{uuid4()}")

    assert response.status_code == 201
    payload = response.json()
    assert payload["session"]["status"] == TailoringStatus.COMPLETED.value
    assert payload["resume_version"]["ats_score"] == 92
    assert payload["cover_letter"]["title"] == "Senior Backend Engineer"


def test_list_tailoring_history_success(tmp_path: Path) -> None:
    user_id = uuid4()
    service_stub = _TailoringServiceStub(owner_id=user_id)
    export_stub = _ExportServiceStub(
        owner_id=user_id,
        resume_export_path=tmp_path / "tailored.md",
        letter_export_path=tmp_path / "cover-letter.md",
    )
    client = _make_client(service_stub, export_stub, user_id)

    response = client.get("/resume-tailoring/history")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == TailoringStatus.COMPLETED.value


def test_get_tailoring_session_ownership_enforced(tmp_path: Path) -> None:
    owner_id = uuid4()
    other_user_id = uuid4()
    service_stub = _TailoringServiceStub(owner_id=owner_id)
    export_stub = _ExportServiceStub(
        owner_id=owner_id,
        resume_export_path=tmp_path / "tailored.md",
        letter_export_path=tmp_path / "cover-letter.md",
    )
    client = _make_client(service_stub, export_stub, other_user_id)

    response = client.get(f"/resume-tailoring/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Tailoring session not found"


def test_get_tailored_resume_success(tmp_path: Path) -> None:
    user_id = uuid4()
    service_stub = _TailoringServiceStub(owner_id=user_id)
    export_stub = _ExportServiceStub(
        owner_id=user_id,
        resume_export_path=tmp_path / "tailored.md",
        letter_export_path=tmp_path / "cover-letter.md",
    )
    client = _make_client(service_stub, export_stub, user_id)

    response = client.get(f"/resume-tailoring/{service_stub.session.id}/resume")

    assert response.status_code == 200
    assert response.json()["professional_summary"] == "Tailored summary"


def test_get_cover_letter_success(tmp_path: Path) -> None:
    user_id = uuid4()
    service_stub = _TailoringServiceStub(owner_id=user_id)
    export_stub = _ExportServiceStub(
        owner_id=user_id,
        resume_export_path=tmp_path / "tailored.md",
        letter_export_path=tmp_path / "cover-letter.md",
    )
    client = _make_client(service_stub, export_stub, user_id)

    response = client.get(f"/resume-tailoring/{service_stub.session.id}/cover-letter")

    assert response.status_code == 200
    assert response.json()["title"] == "Senior Backend Engineer"


def test_delete_tailoring_session_success(tmp_path: Path) -> None:
    user_id = uuid4()
    service_stub = _TailoringServiceStub(owner_id=user_id)
    export_stub = _ExportServiceStub(
        owner_id=user_id,
        resume_export_path=tmp_path / "tailored.md",
        letter_export_path=tmp_path / "cover-letter.md",
    )
    client = _make_client(service_stub, export_stub, user_id)

    response = client.delete(f"/resume-tailoring/{service_stub.session.id}")

    assert response.status_code == 204


def test_export_resume_success(tmp_path: Path) -> None:
    user_id = uuid4()
    resume_export_path = tmp_path / "tailored.md"
    resume_export_path.write_text("# Tailored Resume\n", encoding="utf-8")
    letter_export_path = tmp_path / "cover-letter.md"
    letter_export_path.write_text("# Cover Letter\n", encoding="utf-8")

    service_stub = _TailoringServiceStub(owner_id=user_id)
    export_stub = _ExportServiceStub(
        owner_id=user_id,
        resume_export_path=resume_export_path,
        letter_export_path=letter_export_path,
    )
    client = _make_client(service_stub, export_stub, user_id)

    response = client.get(f"/export/resume/{uuid4()}?format=md")

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert b"Tailored Resume" in response.content


def test_export_cover_letter_success(tmp_path: Path) -> None:
    user_id = uuid4()
    resume_export_path = tmp_path / "tailored.md"
    resume_export_path.write_text("# Tailored Resume\n", encoding="utf-8")
    letter_export_path = tmp_path / "cover-letter.md"
    letter_export_path.write_text("# Cover Letter\n", encoding="utf-8")

    service_stub = _TailoringServiceStub(owner_id=user_id)
    export_stub = _ExportServiceStub(
        owner_id=user_id,
        resume_export_path=resume_export_path,
        letter_export_path=letter_export_path,
    )
    client = _make_client(service_stub, export_stub, user_id)

    response = client.get(f"/export/cover-letter/{uuid4()}?format=md")

    assert response.status_code == 200
    assert b"Cover Letter" in response.content


def test_export_format_validation_error(tmp_path: Path) -> None:
    user_id = uuid4()
    resume_export_path = tmp_path / "tailored.md"
    resume_export_path.write_text("# Tailored Resume\n", encoding="utf-8")
    letter_export_path = tmp_path / "cover-letter.md"
    letter_export_path.write_text("# Cover Letter\n", encoding="utf-8")

    service_stub = _TailoringServiceStub(owner_id=user_id)
    export_stub = _ExportServiceStub(
        owner_id=user_id,
        resume_export_path=resume_export_path,
        letter_export_path=letter_export_path,
    )
    export_stub.invalid_format = True
    client = _make_client(service_stub, export_stub, user_id)

    response = client.get(f"/export/resume/{uuid4()}?format=exe")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported export format"
