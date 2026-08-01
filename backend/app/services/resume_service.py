"""Business logic orchestration for the resume domain."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from app.config.settings import settings
from app.core.cache import RedisCache
from app.core.exceptions import (
    FileTooLargeException,
    ResumeNotFoundException,
    UnsupportedFileTypeException,
)
from app.core.logging import logger
from app.enums import ResumeFileType
from app.models.resume import Resume
from app.repositories.resume_repository import ResumeRepository
from app.schemas.notification import NotificationCreate
from app.schemas.resume import (
    ResumeListResponse,
    ResumeResponse,
    ResumeUploadResponse,
    ResumeVersionResponse,
)
from app.services.notification_service import NotificationService
from app.storage.base import StorageProvider


class ResumeService:
    """Orchestrates resume storage and persistence.

    All resume business rules (upload validation, versioning, ownership
    checks) live here. This service is the only component allowed to
    coordinate the ``ResumeRepository`` (database) and ``StorageProvider``
    (filesystem) together; neither collaborator accesses the other.
    """

    def __init__(
        self,
        resume_repository: ResumeRepository,
        storage_provider: StorageProvider,
        notification_service: NotificationService | None = None,
        cache_service: Any | None = None,
    ) -> None:
        self._resumes = resume_repository
        self._storage = storage_provider
        self._notifications = notification_service
        redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
        redis_enabled = bool(getattr(settings, "redis_enabled", False))
        default_ttl_seconds = int(getattr(settings, "cache_default_ttl_seconds", 300))
        self._cache = cache_service or RedisCache(
            redis_url=redis_url,
            default_ttl_seconds=default_ttl_seconds,
            enabled=redis_enabled,
        )

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

        if self._notifications is not None:
            await self._notifications.create_notification(
                user_id=user_id,
                payload=NotificationCreate(
                    title="Resume uploaded",
                    message=f"{title} was uploaded successfully.",
                    type="resume_uploaded",
                    priority="medium",
                    action_url=f"/resumes/{resume.id}",
                    metadata_json={
                        "resume_id": str(resume.id),
                        "version_id": str(version.id),
                        "entity_id": str(resume.id),
                    },
                ),
            )

        await self._invalidate_resume_cache(user_id=user_id)

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

        await self._invalidate_resume_cache(user_id=user_id, resume_id=resume_id)

        return ResumeVersionResponse.model_validate(version)

    async def list_user_resumes(self, user_id: UUID) -> ResumeListResponse:
        """Return all resumes owned by a user.

        Args:
            user_id: Owning user's primary key.

        Returns:
            Wrapped list of resumes with a total count.
        """
        cached = await self._cache_get(
            namespace=self._list_namespace(user_id),
            key="all",
        )
        if cached is not None:
            return ResumeListResponse.model_validate(cached)

        resumes = await self._resumes.list_by_user(user_id)
        response = ResumeListResponse(
            items=[ResumeResponse.model_validate(resume) for resume in resumes],
            total=len(resumes),
        )
        await self._cache_set(
            namespace=self._list_namespace(user_id),
            key="all",
            value=response.model_dump(mode="json"),
            ttl_seconds=self._ttl_seconds(),
        )
        return response

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
        cached = await self._cache_get(
            namespace=self._detail_namespace(user_id),
            key=str(resume_id),
        )
        if cached is not None:
            return ResumeResponse.model_validate(cached)

        resume = await self._get_owned_resume(user_id=user_id, resume_id=resume_id)
        response = ResumeResponse.model_validate(resume)
        await self._cache_set(
            namespace=self._detail_namespace(user_id),
            key=str(resume_id),
            value=response.model_dump(mode="json"),
            ttl_seconds=self._ttl_seconds(),
        )
        return response

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
        loaded_versions = getattr(resume, "versions", None)
        if loaded_versions is not None:
            versions = list(loaded_versions)
        else:
            versions = await self._resumes.get_versions(resume_id)
        await self._resumes.delete(resume.id, resume=resume)
        for version in versions:
            if version.file_path:
                self._storage.delete(version.file_path)
        await self._invalidate_resume_cache(user_id=user_id, resume_id=resume_id)

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

        cache_key = (
            f"version:{version_id}" if version_id is not None else "version:latest"
        )
        cached_path = await self._cache_get(
            namespace=self._download_namespace(user_id, resume_id),
            key=cache_key,
        )
        if isinstance(cached_path, str):
            return Path(cached_path)

        download_path = self._storage.get_download_path(version.file_path)
        await self._cache_set(
            namespace=self._download_namespace(user_id, resume_id),
            key=cache_key,
            value=str(download_path),
            ttl_seconds=self._ttl_seconds(),
        )
        return download_path

    async def _invalidate_resume_cache(
        self,
        *,
        user_id: UUID,
        resume_id: UUID | None = None,
    ) -> None:
        await self._cache_delete_pattern(self._list_pattern(user_id))
        await self._cache_delete_pattern(self._detail_pattern(user_id))
        if resume_id is not None:
            await self._cache_delete_pattern(self._download_pattern(user_id, resume_id))
        else:
            await self._cache_delete_pattern(self._download_pattern(user_id))

    def _list_namespace(self, user_id: UUID) -> str:
        return f"resume:list:{user_id}"

    def _list_pattern(self, user_id: UUID) -> str:
        return f"{self._list_namespace(user_id)}:*"

    def _detail_namespace(self, user_id: UUID) -> str:
        return f"resume:detail:{user_id}"

    def _detail_pattern(self, user_id: UUID) -> str:
        return f"{self._detail_namespace(user_id)}:*"

    def _download_namespace(self, user_id: UUID, resume_id: UUID | None = None) -> str:
        if resume_id is None:
            return f"resume:download:{user_id}"
        return f"resume:download:{user_id}:{resume_id}"

    def _download_pattern(self, user_id: UUID, resume_id: UUID | None = None) -> str:
        return f"{self._download_namespace(user_id, resume_id)}:*"

    def _cache_key(self, namespace: str, key: str) -> str:
        return f"{namespace}:{key}"

    def _ttl_seconds(self) -> int:
        configured = int(getattr(settings, "cache_default_ttl_seconds", 300))
        return max(300, min(configured, 600))

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
