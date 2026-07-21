from fastapi import APIRouter

from .routes.analysis import router as analysis_router
from .routes.auth import router as auth_router
from .routes.chat import router as chat_router
from .routes.health import router as health_router
from .routes.resume import router as resume_router
from .routes.users import router as users_router

router = APIRouter()

router.include_router(chat_router)
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(analysis_router)
router.include_router(resume_router)
router.include_router(users_router)
