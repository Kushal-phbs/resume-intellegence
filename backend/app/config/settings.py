"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "AI Project Template"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3-32b"

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


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


# Singleton settings instance
settings = get_settings()
