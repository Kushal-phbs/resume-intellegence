"""Storage abstraction package."""

from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider

__all__ = ["StorageProvider", "LocalStorageProvider"]
