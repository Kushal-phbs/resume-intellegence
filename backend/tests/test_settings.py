from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_settings_env_file_path_is_resolved_relative_to_backend() -> None:
    expected = Path(__file__).resolve().parents[1] / ".env"
    env_file = Settings.model_config["env_file"]

    assert Path(env_file).resolve() == expected.resolve()


def _valid_settings_kwargs(**overrides: object) -> dict:
    """Return the minimal kwargs needed to satisfy every settings validator."""
    kwargs: dict = {
        "groq_api_key": "test-key",
        "groq_model": "test-model",
        "database_url": "postgresql+asyncpg://user:pass@localhost:5432/db",
        "secret_key": "a" * 32,
    }
    kwargs.update(overrides)
    return kwargs


def test_settings_accepts_valid_security_configuration() -> None:
    result = Settings(_env_file=None, **_valid_settings_kwargs())

    assert result.jwt_algorithm == "HS256"
    assert result.access_token_expire_minutes == 15
    assert result.refresh_token_expire_days == 7
    assert result.groq_base_url == "https://api.groq.com/openai/v1"
    assert result.groq_http_timeout == 30
    assert result.groq_max_retries == 3


def test_settings_rejects_missing_secret_key() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY must be configured"):
        Settings(_env_file=None, **_valid_settings_kwargs(secret_key=""))


def test_settings_rejects_short_secret_key() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY must be at least"):
        Settings(_env_file=None, **_valid_settings_kwargs(secret_key="too-short"))


def test_settings_rejects_unsupported_jwt_algorithm() -> None:
    with pytest.raises(ValidationError, match="is not supported"):
        Settings(_env_file=None, **_valid_settings_kwargs(jwt_algorithm="none"))


def test_settings_rejects_non_positive_access_token_expiry() -> None:
    with pytest.raises(
        ValidationError, match="ACCESS_TOKEN_EXPIRE_MINUTES must be a positive"
    ):
        Settings(
            _env_file=None,
            **_valid_settings_kwargs(access_token_expire_minutes=0),
        )


def test_settings_rejects_non_positive_refresh_token_expiry() -> None:
    with pytest.raises(
        ValidationError, match="REFRESH_TOKEN_EXPIRE_DAYS must be a positive"
    ):
        Settings(_env_file=None, **_valid_settings_kwargs(refresh_token_expire_days=-1))
