"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_SUPPORTED_JWT_ALGORITHMS = {
    "HS256",
    "HS384",
    "HS512",
    "RS256",
    "RS384",
    "RS512",
    "ES256",
    "ES384",
    "ES512",
}

_MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "AI Project Template"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3-32b"

    database_url: str = ""
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10

    secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("*", mode="before")
    @classmethod
    def _strip_whitespace(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def _validate_llm_settings(self) -> "Settings":
        if not self.llm_provider:
            raise ValueError("LLM provider must be configured in llm_provider.")

        provider = self.llm_provider.lower()
        if provider == "groq":
            if not self.groq_api_key:
                raise ValueError(
                    "GROQ_API_KEY must be set when llm_provider is 'groq'."
                )
            if not self.groq_model:
                raise ValueError("GROQ_MODEL must be set when llm_provider is 'groq'.")

        return self

    @model_validator(mode="after")
    def _validate_database_settings(self) -> "Settings":
        if not self.database_url:
            raise ValueError("DATABASE_URL must be configured.")

        if not self.database_url.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the 'postgresql+asyncpg://' driver scheme."
            )

        return self

    @model_validator(mode="after")
    def _validate_security_settings(self) -> "Settings":
        if not self.secret_key:
            raise ValueError("SECRET_KEY must be configured.")

        if len(self.secret_key) < _MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY must be at least {_MIN_SECRET_KEY_LENGTH} characters long."
            )

        if self.jwt_algorithm not in _SUPPORTED_JWT_ALGORITHMS:
            supported = ", ".join(sorted(_SUPPORTED_JWT_ALGORITHMS))
            raise ValueError(
                f"JWT_ALGORITHM '{self.jwt_algorithm}' is not supported. "
                f"Supported algorithms: {supported}."
            )

        if self.access_token_expire_minutes <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer.")

        if self.refresh_token_expire_days <= 0:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be a positive integer.")

        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


# Singleton settings instance
settings = get_settings()
