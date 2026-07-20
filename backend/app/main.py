from fastapi import FastAPI

from app.api.router import router as api_router
from app.core.handlers import register_exception_handlers
from app.core.lifespan import lifespan
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware

# Configure logging before creating the application so any startup logs are formatted
setup_logging()

app = FastAPI(
    title="AI Project Template",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)

# Register global exception handlers
register_exception_handlers(app)

app.include_router(api_router)
