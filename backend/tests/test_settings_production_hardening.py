from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def _base_valid_kwargs() -> dict[str, object]:
    return {
        "groq_api_key": "test-key",
        "groq_model": "test-model",
        "database_url": "postgresql+asyncpg://user:pass@localhost:5432/db",
        "secret_key": "a" * 32,
    }


def test_settings_reject_invalid_redis_url_scheme() -> None:
    with pytest.raises(ValidationError, match="REDIS_URL must start"):
        Settings(_env_file=None, **_base_valid_kwargs(), redis_url="http://redis")


def test_settings_reject_non_positive_cache_ttl() -> None:
    with pytest.raises(ValidationError, match="cache TTL"):
        Settings(
            _env_file=None,
            **_base_valid_kwargs(),
            cache_default_ttl_seconds=0,
        )


def test_settings_reject_non_positive_rate_limit_window() -> None:
    with pytest.raises(ValidationError, match="RATE_LIMIT_WINDOW_SECONDS"):
        Settings(
            _env_file=None,
            **_base_valid_kwargs(),
            rate_limit_window_seconds=0,
        )


def test_settings_reject_invalid_pool_timeout() -> None:
    with pytest.raises(ValidationError, match="DB_POOL_TIMEOUT_SECONDS"):
        Settings(
            _env_file=None,
            **_base_valid_kwargs(),
            db_pool_timeout_seconds=0,
        )


def test_settings_reject_invalid_groq_base_url() -> None:
    with pytest.raises(ValidationError, match="GROQ_BASE_URL"):
        Settings(
            _env_file=None,
            **_base_valid_kwargs(),
            groq_base_url="ftp://api.groq.com/openai/v1",
        )


def test_settings_reject_non_positive_groq_timeout() -> None:
    with pytest.raises(ValidationError, match="GROQ_HTTP_TIMEOUT"):
        Settings(
            _env_file=None,
            **_base_valid_kwargs(),
            groq_http_timeout=0,
        )


def test_settings_reject_negative_groq_max_retries() -> None:
    with pytest.raises(ValidationError, match="GROQ_MAX_RETRIES"):
        Settings(
            _env_file=None,
            **_base_valid_kwargs(),
            groq_max_retries=-1,
        )
