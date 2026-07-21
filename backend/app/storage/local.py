"""Local filesystem storage provider implementation."""

from __future__ import annotations

import uuid
from pathlib import Path

from app.core.exceptions import StorageException, StorageFileNotFoundException
from app.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """Stores files on the local filesystem under a configurable directory.

    Generated storage keys are always unique (never overwrite existing
    files) and every path is resolved and validated to stay within the
    configured base directory to guard against path traversal.
    """

    def __init__(self, base_directory: str | Path) -> None:
        """Create the provider, creating the base directory if needed.

        Args:
            base_directory: Root directory under which files are stored.
        """
        self._base_dir = Path(base_directory).resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, *, content: bytes, filename: str) -> str:
        """Persist ``content`` under a newly generated unique storage key."""
        extension = Path(filename).suffix
        storage_key = f"{uuid.uuid4().hex}{extension}"
        while self.exists(storage_key):
            storage_key = f"{uuid.uuid4().hex}{extension}"

        path = self._resolve_path(storage_key)
        path.write_bytes(content)
        return storage_key

    def read(self, storage_key: str) -> bytes:
        """Read and return the raw bytes stored under ``storage_key``."""
        path = self._resolve_path(storage_key)
        if not path.is_file():
            raise StorageFileNotFoundException()
        return path.read_bytes()

    def delete(self, storage_key: str) -> None:
        """Delete the file stored under ``storage_key`` if it exists."""
        path = self._resolve_path(storage_key)
        if path.is_file():
            path.unlink()

    def exists(self, storage_key: str) -> bool:
        """Return whether ``storage_key`` refers to an existing file."""
        path = self._resolve_path(storage_key)
        return path.is_file()

    def get_download_path(self, storage_key: str) -> Path:
        """Return the absolute filesystem path for ``storage_key``."""
        path = self._resolve_path(storage_key)
        if not path.is_file():
            raise StorageFileNotFoundException()
        return path

    def _resolve_path(self, storage_key: str) -> Path:
        """Resolve ``storage_key`` to an absolute path within the base dir.

        Guards against path traversal by rejecting any key that resolves
        outside of the configured base directory.
        """
        candidate = (self._base_dir / storage_key).resolve()
        if candidate != self._base_dir and self._base_dir not in candidate.parents:
            raise StorageException(message="Invalid storage key")
        return candidate
