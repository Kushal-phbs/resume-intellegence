from __future__ import annotations

import pytest

from app.core.exceptions import StorageException, StorageFileNotFoundException
from app.storage.local import LocalStorageProvider


def test_init_creates_base_directory(tmp_path) -> None:
    target = tmp_path / "nested" / "uploads"

    LocalStorageProvider(base_directory=target)

    assert target.is_dir()


def test_save_persists_content_and_returns_unique_key(tmp_path) -> None:
    provider = LocalStorageProvider(base_directory=tmp_path)

    key = provider.save(content=b"hello world", filename="resume.pdf")

    assert key.endswith(".pdf")
    assert provider.exists(key)
    assert provider.read(key) == b"hello world"


def test_save_never_overwrites_existing_file(tmp_path) -> None:
    provider = LocalStorageProvider(base_directory=tmp_path)

    key_one = provider.save(content=b"first", filename="resume.pdf")
    key_two = provider.save(content=b"second", filename="resume.pdf")

    assert key_one != key_two
    assert provider.read(key_one) == b"first"
    assert provider.read(key_two) == b"second"


def test_read_missing_file_raises_not_found(tmp_path) -> None:
    provider = LocalStorageProvider(base_directory=tmp_path)

    with pytest.raises(StorageFileNotFoundException):
        provider.read("does-not-exist.pdf")


def test_delete_removes_file(tmp_path) -> None:
    provider = LocalStorageProvider(base_directory=tmp_path)
    key = provider.save(content=b"data", filename="resume.pdf")

    provider.delete(key)

    assert not provider.exists(key)


def test_delete_missing_file_is_a_no_op(tmp_path) -> None:
    provider = LocalStorageProvider(base_directory=tmp_path)

    provider.delete("does-not-exist.pdf")


def test_exists_returns_false_for_missing_file(tmp_path) -> None:
    provider = LocalStorageProvider(base_directory=tmp_path)

    assert provider.exists("does-not-exist.pdf") is False


def test_get_download_path_returns_absolute_path(tmp_path) -> None:
    provider = LocalStorageProvider(base_directory=tmp_path)
    key = provider.save(content=b"data", filename="resume.pdf")

    path = provider.get_download_path(key)

    assert path.is_file()
    assert path.read_bytes() == b"data"


def test_get_download_path_missing_file_raises_not_found(tmp_path) -> None:
    provider = LocalStorageProvider(base_directory=tmp_path)

    with pytest.raises(StorageFileNotFoundException):
        provider.get_download_path("does-not-exist.pdf")


def test_path_traversal_is_rejected(tmp_path) -> None:
    provider = LocalStorageProvider(base_directory=tmp_path)

    with pytest.raises(StorageException):
        provider.read("../outside.txt")
