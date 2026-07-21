from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.resume import router as resume_router
from app.core.exceptions import (
    FileTooLargeException,
    ResumeNotFoundException,
    StorageFileNotFoundException,
    UnsupportedFileTypeException,
)
from app.core.handlers import register_exception_handlers
from app.dependencies.auth import get_current_user
from app.dependencies.resume import get_resume_service
from app.enums import ResumeFileType, ResumeStatus
from app.schemas.resume import (
    ResumeListResponse,
    ResumeResponse,
    ResumeUploadResponse,
    ResumeVersionResponse,
)


class _ResumeServiceStub:
    def __init__(
        self,
        owner_id: object,
        existing_resume_ids: set[object] | None = None,
        missing_file_ids: set[object] | None = None,
    ) -> None:
        self.owner_id = owner_id
        self.deleted_resumes: list[object] = []
        self.upload_calls: list[dict[str, object]] = []
        self.existing_resume_ids = existing_resume_ids or set()
        self.missing_file_ids = missing_file_ids or set()
        self.download_path = Path("/tmp/resume.pdf")

    async def upload_resume(
        self,
        *,
        user_id: object,
        title: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> ResumeUploadResponse:
        self.upload_calls.append(
            {
                "user_id": user_id,
                "title": title,
                "filename": filename,
                "content_type": content_type,
                "content": content,
            }
        )
        if not filename.endswith((".pdf", ".doc", ".docx", ".txt")):
            raise UnsupportedFileTypeException("Unsupported file extension: .exe")
        if content_type == "text/plain":
            raise UnsupportedFileTypeException("Unsupported content type: text/plain")
        if len(content) > 1_000:
            raise FileTooLargeException()

        now = datetime.now(UTC)
        resume_id = uuid4()
        version_id = uuid4()
        resume = ResumeResponse(
            id=resume_id,
            user_id=user_id,
            title=title,
            is_primary=False,
            created_at=now,
            updated_at=now,
        )
        version = ResumeVersionResponse(
            id=version_id,
            resume_id=resume_id,
            version_number=1,
            content="",
            file_path="storage-key.pdf",
            created_at=now,
            updated_at=now,
        )
        return ResumeUploadResponse(
            resume=resume,
            version=version,
            status=ResumeStatus.ACTIVE,
            file_type=ResumeFileType.PDF,
        )

    async def list_user_resumes(self, user_id: object) -> ResumeListResponse:
        if user_id == "empty":
            return ResumeListResponse(items=[], total=0)

        now = datetime.now(UTC)
        first = ResumeResponse(
            id=uuid4(),
            user_id=user_id,
            title="Resume 1",
            is_primary=False,
            created_at=now,
            updated_at=now,
        )
        second = ResumeResponse(
            id=uuid4(),
            user_id=user_id,
            title="Resume 2",
            is_primary=True,
            created_at=now,
            updated_at=now,
        )
        return ResumeListResponse(items=[first, second], total=2)

    async def get_resume(self, *, user_id: object, resume_id: object) -> ResumeResponse:
        if user_id != self.owner_id:
            raise ResumeNotFoundException()
        if self.existing_resume_ids and resume_id not in self.existing_resume_ids:
            raise ResumeNotFoundException()
        now = datetime.now(UTC)
        return ResumeResponse(
            id=resume_id,
            user_id=user_id,
            title="Resume 1",
            is_primary=False,
            created_at=now,
            updated_at=now,
        )

    async def get_download_path(
        self, *, user_id: object, resume_id: object, version_id: object | None = None
    ) -> Path:
        if user_id != self.owner_id:
            raise ResumeNotFoundException()
        if resume_id in self.missing_file_ids:
            raise StorageFileNotFoundException()
        return Path(self.download_path)

    async def delete_resume(self, *, user_id: object, resume_id: object) -> None:
        if user_id != self.owner_id:
            raise ResumeNotFoundException()
        if resume_id in self.deleted_resumes:
            raise ResumeNotFoundException()
        self.deleted_resumes.append(resume_id)


def _build_app(service_stub: _ResumeServiceStub, current_user_id: object) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(resume_router)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=current_user_id
    )
    app.dependency_overrides[get_resume_service] = lambda: service_stub
    return app


def _make_client(
    service_stub: _ResumeServiceStub, current_user_id: object
) -> TestClient:
    return TestClient(_build_app(service_stub, current_user_id))


def test_upload_resume_route_success() -> None:
    user_id = uuid4()
    service_stub = _ResumeServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.post(
        "/resumes/upload",
        data={"title": "My Resume"},
        files={"file": ("resume.pdf", b"file-bytes", "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["file_type"] == ResumeFileType.PDF.value
    assert response.json()["status"] == ResumeStatus.ACTIVE.value
    assert service_stub.upload_calls[0]["filename"] == "resume.pdf"


def test_upload_resume_route_invalid_extension() -> None:
    user_id = uuid4()
    service_stub = _ResumeServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.post(
        "/resumes/upload",
        data={"title": "My Resume"},
        files={"file": ("resume.exe", b"file-bytes", "application/octet-stream")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported file extension: .exe"


def test_upload_resume_route_invalid_mime_type() -> None:
    user_id = uuid4()
    service_stub = _ResumeServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.post(
        "/resumes/upload",
        data={"title": "My Resume"},
        files={"file": ("resume.pdf", b"file-bytes", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported content type: text/plain"


def test_upload_resume_route_oversized_file() -> None:
    user_id = uuid4()
    service_stub = _ResumeServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.post(
        "/resumes/upload",
        data={"title": "My Resume"},
        files={"file": ("resume.pdf", b"x" * 1_001, "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Uploaded file exceeds maximum allowed size"


def test_list_resumes_route_empty_list() -> None:
    service_stub = _ResumeServiceStub(owner_id="empty")
    client = _make_client(service_stub, "empty")

    response = client.get("/resumes")

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_list_resumes_route_multiple_resumes() -> None:
    user_id = uuid4()
    service_stub = _ResumeServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get("/resumes")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2


def test_get_resume_route_existing() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _ResumeServiceStub(
        owner_id=user_id,
        existing_resume_ids={resume_id},
    )
    client = _make_client(service_stub, user_id)

    response = client.get(f"/resumes/{resume_id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(resume_id)


def test_get_resume_route_missing() -> None:
    user_id = uuid4()
    _existing_resume_id = uuid4()
    service_stub = _ResumeServiceStub(
        owner_id=user_id,
        existing_resume_ids={_existing_resume_id},
    )
    client = _make_client(service_stub, user_id)
    missing_resume_id = uuid4()

    response = client.get(f"/resumes/{missing_resume_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"


def test_get_resume_route_unauthorized() -> None:
    owner_id = uuid4()
    other_user_id = uuid4()
    service_stub = _ResumeServiceStub(owner_id=owner_id)
    client = _make_client(service_stub, other_user_id)

    response = client.get(f"/resumes/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"


def test_download_resume_route_success(tmp_path) -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _ResumeServiceStub(
        owner_id=user_id,
        existing_resume_ids={resume_id},
    )
    service_stub.download_path = tmp_path / "resume.pdf"
    service_stub.download_path.write_bytes(b"download-bytes")
    client = _make_client(service_stub, user_id)

    response = client.get(f"/resumes/{resume_id}/download")

    assert response.status_code == 200
    assert response.content == b"download-bytes"
    assert response.headers["content-type"].startswith("application/")


def test_download_resume_route_missing_file() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _ResumeServiceStub(
        owner_id=user_id,
        missing_file_ids={resume_id},
        existing_resume_ids={resume_id},
    )
    client = _make_client(service_stub, user_id)

    response = client.get(f"/resumes/{resume_id}/download")

    assert response.status_code == 404
    assert response.json()["detail"] == "Stored file not found"


def test_download_resume_route_unauthorized() -> None:
    owner_id = uuid4()
    other_user_id = uuid4()
    service_stub = _ResumeServiceStub(owner_id=owner_id)
    client = _make_client(service_stub, other_user_id)

    response = client.get(f"/resumes/{uuid4()}/download")

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"


def test_delete_resume_route_success() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _ResumeServiceStub(
        owner_id=user_id,
        existing_resume_ids={resume_id},
    )
    client = _make_client(service_stub, user_id)

    response = client.delete(f"/resumes/{resume_id}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_resume_route_repeated_delete() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _ResumeServiceStub(
        owner_id=user_id,
        existing_resume_ids={resume_id},
    )
    client = _make_client(service_stub, user_id)

    first = client.delete(f"/resumes/{resume_id}")
    second = client.delete(f"/resumes/{resume_id}")

    assert first.status_code == 204
    assert second.status_code == 404
    assert second.json()["detail"] == "Resume not found"


def test_delete_resume_route_unauthorized() -> None:
    owner_id = uuid4()
    other_user_id = uuid4()
    service_stub = _ResumeServiceStub(owner_id=owner_id)
    client = _make_client(service_stub, other_user_id)

    response = client.delete(f"/resumes/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"
