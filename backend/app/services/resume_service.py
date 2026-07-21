"""Business logic orchestration for the resume domain."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.config.settings import settings
from app.core.exceptions import (
    FileTooLargeException,
    ResumeNotFoundException,
    UnsupportedFileTypeException,
)
from app.enums import ResumeFileType
from app.models.resume import Resume
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume import (
    ResumeListResponse,
    ResumeResponse,
    ResumeUploadResponse,
    ResumeVersionResponse,
)
from app.storage.base import StorageProvider


class ResumeService:
    """Orchestrates resume storage and persistence.

    All resume business rules (upload validation, versioning, ownership
    checks) live here. This service is the only component allowed to
    coordinate the ``ResumeRepository`` (database) and ``StorageProvider``
    (filesystem) together; neither collaborator accesses the other.
    """

    def __init__(
        self, resume_repository: ResumeRepository, storage_provider: StorageProvider
    ) -> None:
        self._resumes = resume_repository
        self._storage = storage_provider

    async def upload_resume(
        self,
        *,
        user_id: UUID,
        title: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> ResumeUploadResponse:
        """Validate, store, and persist a new resume and its first version.

        Args:
            user_id: Owning user's primary key.
            title: Human-readable resume title.
            filename: Original uploaded filename.
            content_type: Declared MIME type of the upload.
            content: Raw file bytes.

        Returns:
            Response describing the created resume and its first version.

        Raises:
            UnsupportedFileTypeException: If the extension or content type
                is not in the configured allow-list.
            FileTooLargeException: If the content exceeds the configured
                maximum upload size.
        """
        file_type = self._validate_upload(
            filename=filename, content_type=content_type, content=content
        )

        storage_key = self._storage.save(content=content, filename=filename)
        try:
            resume = await self._resumes.create(user_id=user_id, title=title)
            version = await self._resumes.create_version(
                resume_id=resume.id,
                version_number=1,
                content="",
                file_path=storage_key,
            )
        except Exception:
            self._storage.delete(storage_key)
            if "resume" in locals():
                await self._resumes.delete(resume.id)
            raise

        return ResumeUploadResponse(
            resume=ResumeResponse.model_validate(resume),
            version=ResumeVersionResponse.model_validate(version),
            file_type=file_type,
        )

    async def upload_new_version(
        self,
        *,
        user_id: UUID,
        resume_id: UUID,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> ResumeVersionResponse:
        """Validate, store, and persist a new version of an existing resume.

        Args:
            user_id: Requesting user's primary key (must own the resume).
            resume_id: Resume primary key to add a version to.
            filename: Original uploaded filename.
            content_type: Declared MIME type of the upload.
            content: Raw file bytes.

        Returns:
            Response describing the newly created version.

        Raises:
            ResumeNotFoundException: If the resume does not exist or is not
                owned by ``user_id``.
            UnsupportedFileTypeException: If the extension or content type
                is not in the configured allow-list.
            FileTooLargeException: If the content exceeds the configured
                maximum upload size.
        """
        await self._get_owned_resume(user_id=user_id, resume_id=resume_id)
        self._validate_upload(
            filename=filename, content_type=content_type, content=content
        )

        storage_key = self._storage.save(content=content, filename=filename)
        try:
            latest = await self._resumes.get_latest_version(resume_id)
            next_version_number = (latest.version_number if latest else 0) + 1
            version = await self._resumes.create_version(
                resume_id=resume_id,
                version_number=next_version_number,
                content="",
                file_path=storage_key,
            )
        except Exception:
            self._storage.delete(storage_key)
            raise

        return ResumeVersionResponse.model_validate(version)

    async def list_user_resumes(self, user_id: UUID) -> ResumeListResponse:
        """Return all resumes owned by a user.

        Args:
            user_id: Owning user's primary key.

        Returns:
            Wrapped list of resumes with a total count.
        """
        resumes = await self._resumes.list_by_user(user_id)
        return ResumeListResponse(
            items=[ResumeResponse.model_validate(resume) for resume in resumes],
            total=len(resumes),
        )

    async def get_resume(self, *, user_id: UUID, resume_id: UUID) -> ResumeResponse:
        """Return a single resume owned by a user.

        Args:
            user_id: Requesting user's primary key.
            resume_id: Resume primary key.

        Returns:
            The matching resume.

        Raises:
            ResumeNotFoundException: If the resume does not exist or is not
                owned by ``user_id``.
        """
        resume = await self._get_owned_resume(user_id=user_id, resume_id=resume_id)
        return ResumeResponse.model_validate(resume)

    async def delete_resume(self, *, user_id: UUID, resume_id: UUID) -> None:
        """Delete a resume, its versions, and their stored files.

        Args:
            user_id: Requesting user's primary key.
            resume_id: Resume primary key.

        Raises:
            ResumeNotFoundException: If the resume does not exist or is not
                owned by ``user_id``.
        """
        resume = await self._get_owned_resume(user_id=user_id, resume_id=resume_id)
        versions = await self._resumes.get_versions(resume_id)
        await self._resumes.delete(resume.id)
        for version in versions:
            if version.file_path:
                self._storage.delete(version.file_path)

    async def get_download_path(
        self, *, user_id: UUID, resume_id: UUID, version_id: UUID | None = None
    ) -> Path:
        """Return the filesystem path for a resume's stored file.

        Args:
            user_id: Requesting user's primary key.
            resume_id: Resume primary key.
            version_id: Specific version to download; defaults to the latest.

        Returns:
            Absolute filesystem path to the stored file.

        Raises:
            ResumeNotFoundException: If the resume (or requested version)
                does not exist or is not owned by ``user_id``.
        """
        await self._get_owned_resume(user_id=user_id, resume_id=resume_id)

        if version_id is not None:
            versions = await self._resumes.get_versions(resume_id)
            version = next((v for v in versions if v.id == version_id), None)
        else:
            version = await self._resumes.get_latest_version(resume_id)

        if version is None or not version.file_path:
            raise ResumeNotFoundException(message="Resume version not found")

        return self._storage.get_download_path(version.file_path)

    async def _get_owned_resume(self, *, user_id: UUID, resume_id: UUID) -> Resume:
        resume = await self._resumes.get(resume_id)
        if resume is None or resume.user_id != user_id:
            raise ResumeNotFoundException()
        return resume

    def _validate_upload(
        self, *, filename: str, content_type: str, content: bytes
    ) -> ResumeFileType:
        extension = Path(filename).suffix.lower().lstrip(".")
        if (
            extension not in settings.resume_allowed_extensions
            or extension not in ResumeFileType
        ):
            raise UnsupportedFileTypeException(
                message=f"Unsupported file extension: .{extension}"
            )

        if content_type not in settings.resume_allowed_mime_types:
            raise UnsupportedFileTypeException(
                message=f"Unsupported content type: {content_type}"
            )

        if len(content) > settings.resume_max_upload_size_bytes:
            raise FileTooLargeException()

        return ResumeFileType(extension)
