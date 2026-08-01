"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
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
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_http_timeout: int = 30
    groq_max_retries: int = 3

    database_url: str = ""
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout_seconds: int = 30
    db_pool_recycle_seconds: int = 1800

    secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    jwt_issuer: str | None = None
    jwt_audience: str | None = None

    redis_enabled: bool = True
    redis_url: str = "redis://localhost:6379/0"

    cache_default_ttl_seconds: int = 300
    cache_dashboard_summary_ttl_seconds: int = 120
    cache_dashboard_statistics_ttl_seconds: int = 120
    cache_dashboard_trends_ttl_seconds: int = 180
    cache_dashboard_performance_ttl_seconds: int = 120
    cache_resume_analysis_ttl_seconds: int = 300
    cache_job_analysis_ttl_seconds: int = 300

    rate_limit_enabled: bool = True
    rate_limit_window_seconds: int = 60
    rate_limit_login_requests: int = 10
    rate_limit_register_requests: int = 5
    rate_limit_resume_upload_requests: int = 20
    rate_limit_resume_analysis_requests: int = 20
    rate_limit_job_analysis_requests: int = 20
    rate_limit_resume_tailoring_requests: int = 20
    rate_limit_export_requests: int = 40
    rate_limit_dashboard_refresh_requests: int = 10

    cors_allow_origins_csv: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        validation_alias="CORS_ALLOW_ORIGINS",
    )
    cors_allow_methods_csv: str = Field(
        default="GET,POST,PUT,PATCH,DELETE,OPTIONS",
        validation_alias="CORS_ALLOW_METHODS",
    )
    cors_allow_headers_csv: str = Field(
        default="Authorization,Content-Type,X-Request-ID",
        validation_alias="CORS_ALLOW_HEADERS",
    )
    trusted_hosts_csv: str = Field(
        default="localhost,127.0.0.1,testserver",
        validation_alias="TRUSTED_HOSTS",
    )

    resume_upload_dir: str = "uploads/resumes"
    resume_max_upload_size_mb: int = 5
    resume_allowed_extensions_csv: str = Field(
        default="pdf,doc,docx", validation_alias="RESUME_ALLOWED_EXTENSIONS"
    )
    resume_allowed_mime_types_csv: str = Field(
        default=(
            "application/pdf,application/msword,"
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        validation_alias="RESUME_ALLOWED_MIME_TYPES",
    )

    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.0
    sentry_send_default_pii: bool = False
    sentry_environment: str = ""

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
            if not self.groq_base_url:
                raise ValueError(
                    "GROQ_BASE_URL must be set when llm_provider is 'groq'."
                )
            if not (
                self.groq_base_url.startswith("https://")
                or self.groq_base_url.startswith("http://")
            ):
                raise ValueError("GROQ_BASE_URL must start with http:// or https://")
            if self.groq_http_timeout <= 0:
                raise ValueError("GROQ_HTTP_TIMEOUT must be a positive integer.")
            if self.groq_max_retries < 0:
                raise ValueError("GROQ_MAX_RETRIES must be zero or greater.")

        return self

    @model_validator(mode="after")
    def _validate_database_settings(self) -> "Settings":
        if not self.database_url:
            raise ValueError("DATABASE_URL must be configured.")

        if not self.database_url.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the 'postgresql+asyncpg://' driver scheme."
            )

        if self.db_pool_size <= 0:
            raise ValueError("DB_POOL_SIZE must be a positive integer.")

        if self.db_max_overflow < 0:
            raise ValueError("DB_MAX_OVERFLOW must be zero or greater.")

        if self.db_pool_timeout_seconds <= 0:
            raise ValueError("DB_POOL_TIMEOUT_SECONDS must be a positive integer.")

        if self.db_pool_recycle_seconds <= 0:
            raise ValueError("DB_POOL_RECYCLE_SECONDS must be a positive integer.")

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

        if self.jwt_issuer is not None and not self.jwt_issuer.strip():
            raise ValueError("JWT_ISSUER cannot be blank when configured.")

        if self.jwt_audience is not None and not self.jwt_audience.strip():
            raise ValueError("JWT_AUDIENCE cannot be blank when configured.")

        return self

    @model_validator(mode="after")
    def _validate_redis_cache_settings(self) -> "Settings":
        if self.redis_enabled and not self.redis_url:
            raise ValueError("REDIS_URL must be configured when REDIS_ENABLED=true.")

        if self.redis_url and not (
            self.redis_url.startswith("redis://")
            or self.redis_url.startswith("rediss://")
        ):
            raise ValueError("REDIS_URL must start with redis:// or rediss://")

        ttl_values = [
            self.cache_default_ttl_seconds,
            self.cache_dashboard_summary_ttl_seconds,
            self.cache_dashboard_statistics_ttl_seconds,
            self.cache_dashboard_trends_ttl_seconds,
            self.cache_dashboard_performance_ttl_seconds,
            self.cache_resume_analysis_ttl_seconds,
            self.cache_job_analysis_ttl_seconds,
        ]
        if any(value <= 0 for value in ttl_values):
            raise ValueError("All cache TTL values must be positive integers.")

        return self

    @model_validator(mode="after")
    def _validate_rate_limit_settings(self) -> "Settings":
        if self.rate_limit_window_seconds <= 0:
            raise ValueError("RATE_LIMIT_WINDOW_SECONDS must be a positive integer.")

        limits = [
            self.rate_limit_login_requests,
            self.rate_limit_register_requests,
            self.rate_limit_resume_upload_requests,
            self.rate_limit_resume_analysis_requests,
            self.rate_limit_job_analysis_requests,
            self.rate_limit_resume_tailoring_requests,
            self.rate_limit_export_requests,
            self.rate_limit_dashboard_refresh_requests,
        ]
        if any(value <= 0 for value in limits):
            raise ValueError("All rate-limit values must be positive integers.")

        return self

    @model_validator(mode="after")
    def _validate_resume_settings(self) -> "Settings":
        if not self.resume_upload_dir:
            raise ValueError("RESUME_UPLOAD_DIR must be configured.")

        if self.resume_max_upload_size_mb <= 0:
            raise ValueError("RESUME_MAX_UPLOAD_SIZE_MB must be a positive integer.")

        if not self.resume_allowed_extensions:
            raise ValueError("RESUME_ALLOWED_EXTENSIONS must not be empty.")

        if not self.resume_allowed_mime_types:
            raise ValueError("RESUME_ALLOWED_MIME_TYPES must not be empty.")

        if not self.cors_allow_origins:
            raise ValueError("CORS_ALLOW_ORIGINS must not be empty.")

        if not self.cors_allow_methods:
            raise ValueError("CORS_ALLOW_METHODS must not be empty.")

        if not self.cors_allow_headers:
            raise ValueError("CORS_ALLOW_HEADERS must not be empty.")

        if not self.trusted_hosts:
            raise ValueError("TRUSTED_HOSTS must not be empty.")

        return self

    @property
    def resume_allowed_extensions(self) -> list[str]:
        """Allowed resume file extensions, parsed from a comma-separated list."""
        return [
            item.strip().lower().lstrip(".")
            for item in self.resume_allowed_extensions_csv.split(",")
            if item.strip()
        ]

    @property
    def resume_allowed_mime_types(self) -> list[str]:
        """Allowed resume MIME types, parsed from a comma-separated list."""
        return [
            item.strip()
            for item in self.resume_allowed_mime_types_csv.split(",")
            if item.strip()
        ]

    @property
    def cors_allow_origins(self) -> list[str]:
        """Allowed CORS origins parsed from a comma-separated list."""
        return [
            item.strip()
            for item in self.cors_allow_origins_csv.split(",")
            if item.strip()
        ]

    @property
    def cors_allow_methods(self) -> list[str]:
        """Allowed HTTP methods for CORS."""
        return [
            item.strip().upper()
            for item in self.cors_allow_methods_csv.split(",")
            if item.strip()
        ]

    @property
    def cors_allow_headers(self) -> list[str]:
        """Allowed request headers for CORS."""
        return [
            item.strip()
            for item in self.cors_allow_headers_csv.split(",")
            if item.strip()
        ]

    @property
    def trusted_hosts(self) -> list[str]:
        """Trusted host names parsed from a comma-separated list."""
        return [
            item.strip() for item in self.trusted_hosts_csv.split(",") if item.strip()
        ]

    @property
    def resume_max_upload_size_bytes(self) -> int:
        """Maximum allowed resume upload size, expressed in bytes."""
        return self.resume_max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


# Singleton settings instance
settings = get_settings()
