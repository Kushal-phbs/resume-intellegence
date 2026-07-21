"""Abstract storage provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageProvider(ABC):
    """Abstract interface for file storage backends.

    Implementations are responsible for all filesystem (or remote storage)
    interaction. Callers outside this module must never touch the filesystem
    directly and should only interact with storage through this interface.
    """

    @abstractmethod
    def save(self, *, content: bytes, filename: str) -> str:
        """Persist file content under a new, unique storage key.

        Args:
            content: Raw file bytes to persist.
            filename: Original filename, used to preserve the extension.

        Returns:
            A unique storage key that can be used with the other methods.
        """

    @abstractmethod
    def read(self, storage_key: str) -> bytes:
        """Read and return the raw bytes for a stored file.

        Args:
            storage_key: Key previously returned by :meth:`save`.

        Returns:
            Raw file bytes.
        """

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        """Delete a stored file if it exists.

        Args:
            storage_key: Key previously returned by :meth:`save`.
        """

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """Return whether a storage key refers to an existing file.

        Args:
            storage_key: Key previously returned by :meth:`save`.

        Returns:
            ``True`` if the file exists, otherwise ``False``.
        """

    @abstractmethod
    def get_download_path(self, storage_key: str) -> Path:
        """Return a filesystem path suitable for downloading the file.

        Args:
            storage_key: Key previously returned by :meth:`save`.

        Returns:
            Absolute filesystem path to the stored file.
        """
