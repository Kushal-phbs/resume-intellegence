from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import router as api_router
from app.config import settings
from app.core.handlers import register_exception_handlers
from app.core.lifespan import lifespan
from app.core.logging import setup_logging
from app.core.middleware import (
    ObservabilityMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)

# Configure logging before creating the application so any startup logs are formatted
setup_logging(level="DEBUG" if settings.debug else "INFO")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(RequestIDMiddleware)

# Register global exception handlers
register_exception_handlers(app)

app.include_router(api_router)
